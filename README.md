# Projectizer

Transcribe meeting recordings and generate structured summaries ready for PRD creation, powered by OpenAI Whisper and GPT.

## Features

- **Audio transcription** via OpenAI Whisper API (MP3, WAV, M4A, OGG, WEBM, FLAC, MP4)
- **Multi-file upload** with automatic ordering by file creation date
- **Audio compression** (Opus 32kbps mono) to minimize API costs
- **Smart chunking** for files exceeding Whisper's 25MB limit
- **Structured summaries** with key points, decisions, action items, and next steps
- **Cost estimation** before processing
- **Real-time progress** streaming via SSE

## Prerequisites

- **Python 3.10+**
- **FFmpeg** with libopus support
- **OpenAI API key**

### Install FFmpeg

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Windows (via Chocolatey)
choco install ffmpeg
```

## Quick Start

```bash
git clone https://github.com/aruvr/projectizer.git
cd projectizer
bash run.sh
```

The script automatically creates a virtual environment, installs dependencies, and starts the server at **http://localhost:8899**.

To use a different port:

```bash
PORT=3000 bash run.sh
```

## Configuration

You can set your OpenAI API key in two ways:

1. **From the UI** — click "Impostazioni" (Settings) and paste your key
2. **From file** — copy `config.example.json` to `config.json` and add your key

```bash
cp config.example.json config.json
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `openai_api_key` | — | Your OpenAI API key |
| `summary_model` | `gpt-4o-mini` | Model used for summary generation |

## Project Structure

```
projectizer/
├── app.py              # FastAPI backend
├── static/
│   └── index.html      # Single-page frontend
├── run.sh              # Launch script
├── requirements.txt    # Python dependencies
├── config.example.json # Example configuration
└── config.json         # Local config (gitignored)
```

## Cost Estimates

| Service | Price |
|---------|-------|
| Whisper API | $0.006 / minute |
| GPT-4o-mini (summary) | ~$0.0003 per 30min meeting |

A 1-hour meeting costs roughly **$0.36** for transcription plus a few cents for the summary.

## License

MIT
