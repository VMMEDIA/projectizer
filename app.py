import os
import json
import subprocess
import tempfile
import math
import shutil
import asyncio
import queue
import threading
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
import openai

app = FastAPI(title="Projectizer")

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
CONFIG_FILE = Path("config.json")

MAX_WHISPER_SIZE = 25 * 1024 * 1024  # 25MB


def load_config() -> dict:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}


def save_config(config: dict):
    CONFIG_FILE.write_text(json.dumps(config, indent=2))


def get_openai_client() -> openai.OpenAI:
    config = load_config()
    api_key = config.get("openai_api_key", "")
    if not api_key:
        raise HTTPException(status_code=400, detail="OpenAI API key not configured. Set it in Settings.")
    return openai.OpenAI(api_key=api_key)


def get_audio_info(file_path: str) -> dict:
    """Get duration and creation time from audio metadata via ffprobe."""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", file_path],
        capture_output=True, text=True
    )
    info = json.loads(result.stdout)
    fmt = info.get("format", {})
    tags = fmt.get("tags", {})

    duration = float(fmt.get("duration", 0))

    # Try multiple metadata fields for creation time
    creation_time = (
        tags.get("creation_time")
        or tags.get("date")
        or tags.get("ICRD")  # WAV creation date
        or tags.get("encoded_date")
        or ""
    )

    return {"duration": duration, "creation_time": creation_time}


def get_audio_duration(file_path: str) -> float:
    return get_audio_info(file_path)["duration"]


def compress_audio(input_path: str, output_path: str) -> str:
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", input_path,
            "-vn", "-ac", "1", "-ar", "16000",
            "-c:a", "libopus", "-b:a", "32k",
            output_path
        ],
        capture_output=True, text=True, check=True
    )
    return output_path


def concat_audio(file_paths: list[str], output_path: str) -> str:
    """Concatenate multiple audio files using ffmpeg concat demuxer."""
    list_file = output_path + ".txt"
    with open(list_file, "w") as f:
        for p in file_paths:
            # Escape single quotes in path for ffmpeg concat format
            safe = p.replace("'", "'\\''")
            f.write(f"file '{safe}'\n")
    subprocess.run(
        [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", list_file, "-c", "copy", output_path
        ],
        capture_output=True, text=True, check=True
    )
    os.unlink(list_file)
    return output_path


def split_audio(file_path: str, max_size: int = MAX_WHISPER_SIZE) -> list[str]:
    file_size = os.path.getsize(file_path)
    if file_size <= max_size:
        return [file_path]

    duration = get_audio_duration(file_path)
    num_chunks = math.ceil(file_size / max_size)
    chunk_duration = duration / num_chunks

    chunks = []
    tmp_dir = tempfile.mkdtemp(dir=UPLOAD_DIR)

    for i in range(num_chunks):
        start = i * chunk_duration
        chunk_path = os.path.join(tmp_dir, f"chunk_{i:03d}.ogg")
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", file_path,
                "-ss", str(start), "-t", str(chunk_duration),
                "-c:a", "libopus", "-b:a", "32k",
                "-ac", "1", "-ar", "16000",
                chunk_path
            ],
            capture_output=True, text=True, check=True
        )
        chunks.append(chunk_path)

    return chunks


def transcribe_file(client: openai.OpenAI, file_path: str, language: str | None = None) -> str:
    with open(file_path, "rb") as f:
        kwargs = {"model": "whisper-1", "file": f, "response_format": "text"}
        if language:
            kwargs["language"] = language
        transcript = client.audio.transcriptions.create(**kwargs)
    return transcript


def save_upload(upload_file_content: bytes, suffix: str) -> str:
    """Save uploaded bytes to a temp file and return path."""
    tmp = tempfile.NamedTemporaryFile(dir=UPLOAD_DIR, suffix=suffix, delete=False)
    tmp.write(upload_file_content)
    tmp.close()
    return tmp.name


# --- Routes ---

@app.get("/", response_class=HTMLResponse)
async def index():
    return FileResponse("static/index.html")


@app.get("/api/config")
async def get_config():
    config = load_config()
    has_key = bool(config.get("openai_api_key"))
    return {"has_api_key": has_key}


@app.post("/api/config")
async def set_config(api_key: str = Form(...)):
    config = load_config()
    config["openai_api_key"] = api_key
    save_config(config)
    return {"status": "ok"}


@app.post("/api/estimate")
async def estimate(files: list[UploadFile] = File(...)):
    """Return duration, order, and cost estimate for one or more files."""
    saved = []
    try:
        file_infos = []
        for f in files:
            suffix = Path(f.filename).suffix
            content = await f.read()
            path = save_upload(content, suffix)
            saved.append(path)
            info = get_audio_info(path)
            file_infos.append({
                "name": f.filename,
                "size_mb": round(len(content) / (1024 * 1024), 2),
                "duration_sec": round(info["duration"], 1),
                "creation_time": info["creation_time"],
                "path": path,
            })

        # Sort by creation_time if available, otherwise keep original order
        has_timestamps = all(fi["creation_time"] for fi in file_infos)
        if has_timestamps and len(file_infos) > 1:
            file_infos.sort(key=lambda x: x["creation_time"])
            sort_method = "metadata"
        else:
            sort_method = "original" if not has_timestamps else "metadata"

        total_duration_min = sum(fi["duration_sec"] for fi in file_infos) / 60.0
        total_size_mb = sum(fi["size_mb"] for fi in file_infos)
        whisper_cost = total_duration_min * 0.006
        summary_cost_est = (total_duration_min * 750 * 0.15 + 500 * 0.60) / 1_000_000

        return {
            "files": [
                {"name": fi["name"], "size_mb": fi["size_mb"],
                 "duration_sec": fi["duration_sec"], "creation_time": fi["creation_time"]}
                for fi in file_infos
            ],
            "sort_method": sort_method,
            "total_duration_min": round(total_duration_min, 1),
            "total_size_mb": round(total_size_mb, 2),
            "cost_whisper": round(whisper_cost, 4),
            "cost_summary_est": round(summary_cost_est, 4),
            "cost_total_est": round(whisper_cost + summary_cost_est, 4),
        }
    finally:
        for p in saved:
            if os.path.exists(p):
                os.unlink(p)


# --- SSE Processing ---

def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _process_audio(input_path: str, original_size: int, client: openai.OpenAI,
                   language: str, generate_summary: bool, q: queue.Queue):
    compressed_path = None
    chunks = []
    try:
        q.put(_sse("progress", {"step": "compress", "message": "Compressione audio..."}))
        duration_min = get_audio_duration(input_path) / 60.0
        compressed_path = input_path + ".ogg"
        compress_audio(input_path, compressed_path)
        compressed_size = os.path.getsize(compressed_path)

        q.put(_sse("progress", {"step": "split", "message": "Controllo dimensioni..."}))
        chunks = split_audio(compressed_path)
        num_chunks = len(chunks)

        transcripts = []
        lang = language if language else None
        for i, chunk_path in enumerate(chunks):
            q.put(_sse("progress", {
                "step": "transcribe",
                "message": f"Trascrizione segmento {i + 1}/{num_chunks}...",
                "current": i + 1, "total": num_chunks,
            }))
            text = transcribe_file(client, chunk_path, lang)
            transcripts.append(text)

        full_transcript = "\n".join(transcripts)
        whisper_cost = duration_min * 0.006

        summary = None
        summary_cost = 0.0
        if generate_summary:
            q.put(_sse("progress", {"step": "summary", "message": "Generazione riassunto..."}))
            config = load_config()
            summary_model = config.get("summary_model", "gpt-4o-mini")
            resp = client.chat.completions.create(
                model=summary_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Sei un assistente che crea riassunti strutturati di trascrizioni di riunioni. "
                            "Il riassunto deve essere in italiano e includere:\n"
                            "1. **Punti chiave discussi**\n"
                            "2. **Decisioni prese**\n"
                            "3. **Azioni da intraprendere** (con responsabili se menzionati)\n"
                            "4. **Prossimi passi**\n\n"
                            "Il formato deve essere utile per generare un PRD (Product Requirements Document)."
                        )
                    },
                    {"role": "user", "content": f"Ecco la trascrizione della riunione:\n\n{full_transcript}"}
                ],
            )
            summary = resp.choices[0].message.content
            if resp.usage:
                summary_cost = (resp.usage.prompt_tokens * 0.15 + resp.usage.completion_tokens * 0.60) / 1_000_000

        total_cost = whisper_cost + summary_cost

        q.put(_sse("result", {
            "transcript": full_transcript,
            "summary": summary,
            "stats": {
                "original_size_mb": round(original_size / (1024 * 1024), 2),
                "compressed_size_mb": round(compressed_size / (1024 * 1024), 2),
                "compression_ratio": round((1 - compressed_size / original_size) * 100, 1) if original_size > 0 else 0,
                "chunks": num_chunks,
                "duration_min": round(duration_min, 1),
                "cost_whisper": round(whisper_cost, 4),
                "cost_summary": round(summary_cost, 4),
                "cost_total": round(total_cost, 4),
            }
        }))
    except Exception as e:
        q.put(_sse("error", {"message": str(e)}))
    finally:
        if os.path.exists(input_path):
            os.unlink(input_path)
        if compressed_path and os.path.exists(compressed_path):
            os.unlink(compressed_path)
        for chunk in chunks:
            if compressed_path and chunk != compressed_path and os.path.exists(chunk):
                os.unlink(chunk)
                parent = os.path.dirname(chunk)
                if parent != str(UPLOAD_DIR) and os.path.isdir(parent):
                    shutil.rmtree(parent, ignore_errors=True)
        q.put(None)


@app.post("/api/transcribe")
async def transcribe(
    files: list[UploadFile] = File(...),
    language: str = Form(default=""),
    generate_summary: bool = Form(default=False),
    file_order: str = Form(default=""),
):
    client = get_openai_client()

    # Save all files
    saved_files = []
    for f in files:
        suffix = Path(f.filename).suffix
        content = await f.read()
        path = save_upload(content, suffix)
        saved_files.append({"name": f.filename, "path": path, "size": os.path.getsize(path)})

    # Reorder if explicit order provided (comma-separated filenames)
    if file_order:
        order = [n.strip() for n in file_order.split(",")]
        by_name = {sf["name"]: sf for sf in saved_files}
        saved_files = [by_name[n] for n in order if n in by_name]

    total_original_size = sum(sf["size"] for sf in saved_files)

    # If multiple files, concatenate into one
    if len(saved_files) > 1:
        # First normalize all to same format for concat
        normalized = []
        norm_dir = tempfile.mkdtemp(dir=UPLOAD_DIR)
        for i, sf in enumerate(saved_files):
            norm_path = os.path.join(norm_dir, f"part_{i:03d}.ogg")
            compress_audio(sf["path"], norm_path)
            normalized.append(norm_path)
            os.unlink(sf["path"])

        concat_path = os.path.join(norm_dir, "merged.ogg")
        concat_audio(normalized, concat_path)
        for np in normalized:
            os.unlink(np)

        input_path = concat_path
    else:
        input_path = saved_files[0]["path"]

    q = queue.Queue()
    thread = threading.Thread(
        target=_process_audio,
        args=(input_path, total_original_size, client, language, generate_summary, q),
        daemon=True,
    )
    thread.start()

    async def event_stream():
        while True:
            while True:
                try:
                    msg = q.get_nowait()
                    break
                except queue.Empty:
                    await asyncio.sleep(0.1)
            if msg is None:
                return
            yield msg

    return StreamingResponse(event_stream(), media_type="text/event-stream")


app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8899))
    print(f"\n  Projectizer running at http://localhost:{port}\n")
    uvicorn.run(app, host="0.0.0.0", port=port)
