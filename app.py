import os
import json
import re
import uuid
import subprocess
import tempfile
import math
import shutil
import asyncio
import queue
import threading
from datetime import datetime, timezone
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
SESSIONS_DIR = Path("sessions")
SESSIONS_DIR.mkdir(exist_ok=True)

MAX_WHISPER_SIZE = 25 * 1024 * 1024  # 25MB
_SESSION_ID_RE = re.compile(r"^[a-f0-9]{12}$")

# Pricing (USD). Whisper is duration-billed; diarize is token-billed but
# we keep a per-minute estimate for the cost preview UI. Real cost is
# computed from response.usage at the end of each transcription.
RATE_WHISPER_PER_MIN = 0.006
RATE_DIARIZE_PER_MIN = 0.025  # approximate, calibrated from observed usage
DIARIZE_MODEL = "gpt-4o-transcribe-diarize"


def load_config() -> dict:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}


def save_config(config: dict):
    CONFIG_FILE.write_text(json.dumps(config, indent=2))


# ───── Session storage ──────────────────────────────────────────────────

def _session_path(session_id: str) -> Path:
    if not _SESSION_ID_RE.match(session_id):
        raise HTTPException(status_code=400, detail="Invalid session id")
    return SESSIONS_DIR / f"{session_id}.json"


def save_session(file_names: list[str], transcript: str, summary: Optional[str],
                 stats: dict, language: str, diarized: bool) -> dict:
    """Persist a transcription session to disk and return the saved record."""
    SESSIONS_DIR.mkdir(exist_ok=True)
    session_id = uuid.uuid4().hex[:12]
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    if file_names:
        first_stem = Path(file_names[0]).stem
        title = f"{first_stem} — {now[:10]}"
    else:
        title = f"Sessione {now[:16].replace('T', ' ')}"

    session = {
        "id": session_id,
        "title": title,
        "created_at": now,
        "files": file_names,
        "transcript": transcript,
        "summary": summary,
        "stats": stats,
        "language": language or "auto",
        "diarized": bool(diarized),
    }
    (SESSIONS_DIR / f"{session_id}.json").write_text(
        json.dumps(session, ensure_ascii=False, indent=2)
    )
    return session


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


def transcribe_file(
    client: openai.OpenAI,
    file_path: str,
    language: str | None = None,
    diarize: bool = False,
):
    """Transcribe a single file.

    When ``diarize`` is False, calls ``whisper-1`` and returns a dict with
    ``text``, empty ``segments``, and no ``usage`` info.

    When ``diarize`` is True, calls ``gpt-4o-transcribe-diarize``. Each segment
    in the response carries a ``speaker`` label (``"A"``, ``"B"``, …) that we
    forward to the merger so the UI gets ``Persona 1 / Persona 2`` blocks.
    """
    with open(file_path, "rb") as f:
        if diarize:
            kwargs = {"model": DIARIZE_MODEL, "file": f}
            if language:
                kwargs["language"] = language
            resp = client.audio.transcriptions.create(**kwargs)
            segments = [
                {
                    "start": float(s.start),
                    "end": float(s.end),
                    "text": (s.text or "").strip(),
                    "speaker": s.speaker,
                }
                for s in (resp.segments or [])
            ]
            usage = None
            u = getattr(resp, "usage", None)
            if u is not None:
                u_type = getattr(u, "type", None)
                if u_type == "tokens":
                    usage = {
                        "type": "tokens",
                        "input_tokens": getattr(u, "input_tokens", 0),
                        "output_tokens": getattr(u, "output_tokens", 0),
                    }
                elif u_type == "duration":
                    usage = {"type": "duration", "seconds": getattr(u, "seconds", 0.0)}
            return {
                "text": resp.text,
                "segments": segments,
                "duration": float(getattr(resp, "duration", 0.0) or 0.0),
                "usage": usage,
            }

        kwargs = {"model": "whisper-1", "file": f, "response_format": "text"}
        if language:
            kwargs["language"] = language
        text = client.audio.transcriptions.create(**kwargs)
        return {"text": str(text), "segments": [], "duration": 0.0, "usage": None}


def merge_diarized_segments(segments: list[dict]) -> tuple[str, int]:
    """Group consecutive same-speaker segments into ``Persona N: …`` blocks.

    The diarize model emits speakers as ``"A"``, ``"B"``, … (or ``known_speaker_names``
    if provided). We remap them to ``Persona 1``, ``Persona 2``, … in order of
    first appearance so the UI renders consistently.

    Returns ``(formatted_text, num_unique_speakers)``.
    """
    if not segments:
        return "", 0

    speaker_map: dict[str, int] = {}
    blocks: list[tuple[Optional[int], list[str]]] = []

    for seg in segments:
        spk = seg.get("speaker")
        text = (seg.get("text") or "").strip()
        if not text:
            continue
        if spk and spk not in speaker_map:
            speaker_map[spk] = len(speaker_map) + 1
        persona_num = speaker_map.get(spk) if spk else None
        if blocks and blocks[-1][0] == persona_num:
            blocks[-1][1].append(text)
        else:
            blocks.append((persona_num, [text]))

    lines = []
    for persona_num, texts in blocks:
        body = " ".join(texts).strip()
        if not body:
            continue
        label = f"Persona {persona_num}" if persona_num else "Sconosciuto"
        lines.append(f"{label}: {body}")
    return "\n\n".join(lines), len(speaker_map)


def diarize_cost_from_usage(usage: Optional[dict], duration_min: float) -> float:
    """Compute USD cost from the response.usage of gpt-4o-transcribe-diarize.

    Falls back to a duration-based estimate when usage is missing.
    """
    if not usage:
        return duration_min * RATE_DIARIZE_PER_MIN
    if usage.get("type") == "tokens":
        return (
            usage.get("input_tokens", 0) * (2.50 / 1_000_000)
            + usage.get("output_tokens", 0) * (10.00 / 1_000_000)
        )
    # Duration-billed: assume same per-minute rate as our estimate
    return (usage.get("seconds", 0.0) / 60.0) * RATE_DIARIZE_PER_MIN


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
    return {"has_api_key": bool(config.get("openai_api_key"))}


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
        whisper_cost = total_duration_min * RATE_WHISPER_PER_MIN
        diarize_cost_est = total_duration_min * RATE_DIARIZE_PER_MIN
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
            "cost_diarize_est": round(diarize_cost_est, 4),
            "cost_summary_est": round(summary_cost_est, 4),
            "cost_total_est": round(whisper_cost + summary_cost_est, 4),
            "cost_total_diarize_est": round(diarize_cost_est + summary_cost_est, 4),
        }
    finally:
        for p in saved:
            if os.path.exists(p):
                os.unlink(p)


# --- SSE Processing ---

def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _process_audio(input_path: str, original_size: int, client: openai.OpenAI,
                   language: str, generate_summary: bool, diarize: bool,
                   file_names: list[str], q: queue.Queue):
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

        lang = language if language else None
        transcripts: list[str] = []
        all_segments: list[dict] = []
        cumulative_offset = 0.0
        whisper_cost = 0.0
        for i, chunk_path in enumerate(chunks):
            chunk_label = "Trascrizione + parlanti" if diarize else "Trascrizione"
            q.put(_sse("progress", {
                "step": "transcribe",
                "message": f"{chunk_label} segmento {i + 1}/{num_chunks}...",
                "current": i + 1, "total": num_chunks,
            }))
            result = transcribe_file(client, chunk_path, lang, diarize=diarize)
            transcripts.append(result["text"])

            if diarize:
                # gpt-4o-transcribe-diarize emits its own duration; fall back to ffprobe.
                chunk_dur = result.get("duration") or get_audio_duration(chunk_path)
                # Tag every segment with the cumulative offset so the timeline
                # is continuous across chunks. Speaker labels reset per chunk —
                # OpenAI doesn't expose cross-chunk speaker matching yet, so
                # for files split into multiple chunks the same person may end
                # up tagged differently in each chunk. Single-chunk files (the
                # common case for meetings under ~1.5h compressed) are fine.
                for seg in result["segments"]:
                    all_segments.append({
                        "start": seg["start"] + cumulative_offset,
                        "end": seg["end"] + cumulative_offset,
                        "text": seg["text"],
                        "speaker": seg.get("speaker"),
                    })
                cumulative_offset += chunk_dur
                whisper_cost += diarize_cost_from_usage(result.get("usage"),
                                                       (chunk_dur or 0.0) / 60.0)
            else:
                whisper_cost += (get_audio_duration(chunk_path) / 60.0) * RATE_WHISPER_PER_MIN

        plain_transcript = "\n".join(transcripts)

        # Build the final transcript. With diarize=True the model already
        # gives us speaker-tagged segments — we just regroup into Persona blocks.
        final_transcript = plain_transcript
        num_detected_speakers = 0
        if diarize:
            diarized_text, num_detected_speakers = merge_diarized_segments(all_segments)
            if diarized_text:
                final_transcript = diarized_text

        summary = None
        summary_cost = 0.0
        if generate_summary:
            q.put(_sse("progress", {"step": "summary", "message": "Generazione riassunto..."}))
            config = load_config()
            summary_model = config.get("summary_model", "gpt-4o-mini")
            system_prompt = (
                "Sei un assistente che crea riassunti strutturati di trascrizioni di riunioni. "
                "Il riassunto deve essere in italiano e includere:\n"
                "1. **Punti chiave discussi**\n"
                "2. **Decisioni prese**\n"
                "3. **Azioni da intraprendere** (con responsabili se menzionati)\n"
                "4. **Prossimi passi**\n\n"
                "Il formato deve essere utile per generare un PRD (Product Requirements Document)."
            )
            if diarize and num_detected_speakers > 0:
                system_prompt += (
                    "\n\nLa trascrizione include le etichette dei parlanti "
                    "(es. 'Persona 1:', 'Persona 2:'). Usa queste etichette per attribuire "
                    "opinioni, decisioni e azioni a chi le ha espresse."
                )
            resp = client.chat.completions.create(
                model=summary_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Ecco la trascrizione della riunione:\n\n{final_transcript}"}
                ],
            )
            summary = resp.choices[0].message.content
            if resp.usage:
                summary_cost = (resp.usage.prompt_tokens * 0.15 + resp.usage.completion_tokens * 0.60) / 1_000_000

        total_cost = whisper_cost + summary_cost

        stats = {
            "original_size_mb": round(original_size / (1024 * 1024), 2),
            "compressed_size_mb": round(compressed_size / (1024 * 1024), 2),
            "compression_ratio": round((1 - compressed_size / original_size) * 100, 1) if original_size > 0 else 0,
            "chunks": num_chunks,
            "duration_min": round(duration_min, 1),
            "cost_whisper": round(whisper_cost, 4),
            "cost_summary": round(summary_cost, 4),
            "cost_total": round(total_cost, 4),
        }

        # Persist the session so it shows up in the History tab.
        saved = None
        try:
            saved = save_session(
                file_names=file_names,
                transcript=final_transcript,
                summary=summary,
                stats=stats,
                language=language,
                diarized=bool(diarize),
            )
        except Exception:
            pass  # never block the result on a save error

        q.put(_sse("result", {
            "transcript": final_transcript,
            "summary": summary,
            "diarized": diarize,
            "num_speakers": num_detected_speakers,
            "stats": stats,
            "session": {
                "id": saved["id"] if saved else None,
                "title": saved["title"] if saved else None,
                "created_at": saved["created_at"] if saved else None,
            },
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
    diarize: bool = Form(default=False),
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

    file_names = [sf["name"] for sf in saved_files]

    q = queue.Queue()
    thread = threading.Thread(
        target=_process_audio,
        args=(input_path, total_original_size, client, language, generate_summary,
              diarize, file_names, q),
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


# ───── Sessions API ─────────────────────────────────────────────────────

@app.get("/api/sessions")
async def list_sessions():
    """Return session metadata sorted by creation time (newest first)."""
    if not SESSIONS_DIR.exists():
        return []
    out = []
    for p in SESSIONS_DIR.glob("*.json"):
        try:
            data = json.loads(p.read_text())
            summary = data.get("summary") or data.get("transcript") or ""
            preview = summary.strip().replace("\n", " ")[:180]
            out.append({
                "id": data.get("id"),
                "title": data.get("title"),
                "created_at": data.get("created_at"),
                "duration_min": data.get("stats", {}).get("duration_min"),
                "diarized": data.get("diarized", False),
                "language": data.get("language", ""),
                "preview": preview,
            })
        except Exception:
            continue
    out.sort(key=lambda s: s.get("created_at") or "", reverse=True)
    return out


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    p = _session_path(session_id)
    if not p.exists():
        raise HTTPException(status_code=404, detail="Session not found")
    return json.loads(p.read_text())


@app.patch("/api/sessions/{session_id}")
async def rename_session(session_id: str, title: str = Form(...)):
    p = _session_path(session_id)
    if not p.exists():
        raise HTTPException(status_code=404, detail="Session not found")
    data = json.loads(p.read_text())
    new_title = title.strip()
    if new_title:
        data["title"] = new_title[:200]
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    return {"status": "ok", "title": data["title"]}


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    p = _session_path(session_id)
    if not p.exists():
        raise HTTPException(status_code=404, detail="Session not found")
    p.unlink()
    return {"status": "ok"}


app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8899))
    print(f"\n  Projectizer running at http://localhost:{port}\n")
    uvicorn.run(app, host="0.0.0.0", port=port)
