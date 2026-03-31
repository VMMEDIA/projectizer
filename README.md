<div align="center">

# Projectizer

### The open-source, lightweight alternative to Plaud

Turn any meeting recording into structured, actionable summaries — ready for PRDs, Notion, or your team wiki.

No hardware. No subscription. Just your recordings and an API key.

[![License: MIT](https://img.shields.io/badge/License-MIT-6c5ce7.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-a29bfe.svg)](https://python.org)
[![OpenAI Whisper](https://img.shields.io/badge/OpenAI-Whisper-00b894.svg)](https://platform.openai.com/docs/guides/speech-to-text)

<br>

**$0.36/hour** vs $79/year — you do the math.

</div>

---

## Why Projectizer?

Plaud and similar devices lock you into proprietary hardware, cloud subscriptions, and closed ecosystems.

Projectizer takes a different approach:

| | Plaud | Projectizer |
|---|---|---|
| **Cost** | $79/year subscription + $159 hardware | ~$0.36/hour, pay-as-you-go |
| **Hardware required** | Proprietary device | None — use any phone, laptop, or recorder |
| **Data privacy** | Their cloud, their rules | Runs locally, your API key, your data |
| **Output format** | Locked in their app | Plain text + Markdown — paste anywhere |
| **Customization** | None | Open source — tweak prompts, models, everything |
| **Offline access** | Requires their app | Local web UI, works on any browser |
| **Summary quality** | Fixed AI model | Choose any OpenAI model (GPT-4o, 4o-mini, o1...) |

<br>

> **Record with whatever you already have.** Drop the files into Projectizer. Get your summary. Done.

---

## What You Get

**Transcription** — Whisper-powered, supports 50+ languages with auto-detection. Upload one file or ten — Projectizer concatenates, compresses, and chunks them automatically.

**Structured Summaries** — Not a wall of text. Every summary is organized into key discussion points, decisions made, action items with owners, and next steps. Built for product teams.

**Cost Transparency** — See exactly what you'll pay *before* you hit transcribe. No surprise bills, no hidden tiers.

**Real-Time Progress** — Watch your transcription happen live. Compression, chunking, transcription, summarization — each step streams back to you.

---

## Quick Start

```bash
git clone https://github.com/VMMEDIA/projectizer.git
cd projectizer
bash run.sh
```

That's it. The script creates the virtual environment, installs dependencies, and opens the app at **http://localhost:8899**.

Paste your OpenAI API key in the settings panel and you're ready to go.

### Prerequisites

- Python 3.10+
- FFmpeg (`brew install ffmpeg` on macOS)
- An [OpenAI API key](https://platform.openai.com/api-keys)

---

## How It Works

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Upload     │────▶│  Compress    │────▶│  Transcribe  │────▶│  Summarize   │
│  audio files │     │  Opus 32kbps │     │  Whisper API │     │  GPT-4o-mini │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                                                                       │
       ┌───────────────────────────────────────────────────────────────┘
       ▼
  Structured output:
  • Key points discussed
  • Decisions made
  • Action items (with owners)
  • Next steps
```

**Multi-file uploads** are automatically sorted by creation date metadata — perfect for interrupted recordings or multi-device setups.

**Smart compression** converts any audio format to Opus 32kbps mono before sending to the API, cutting upload size by 80-90% with zero quality loss for speech.

**Chunking** splits files that exceed Whisper's 25MB limit, transcribes each segment, and stitches the results seamlessly.

---

## Cost Breakdown

| What | Cost |
|------|------|
| Transcription (Whisper) | $0.006 / minute |
| Summary (GPT-4o-mini) | ~$0.0003 / meeting |
| **1-hour meeting, total** | **~$0.36** |

For context: 200 hours of meetings per year costs about **$72** — less than one year of Plaud's subscription, with no hardware purchase.

---

## Configuration

Set your API key from the UI or from a config file:

```bash
cp config.example.json config.json
```

```json
{
  "openai_api_key": "sk-...",
  "summary_model": "gpt-4o-mini"
}
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `openai_api_key` | — | Your OpenAI API key |
| `summary_model` | `gpt-4o-mini` | Model for summary generation — swap in `gpt-4o` for higher quality |
| `PORT` (env var) | `8899` | Server port |

---

## Tech Stack

Intentionally minimal. No build step, no bundler, no framework overhead.

- **Backend**: FastAPI + Uvicorn
- **Frontend**: Vanilla HTML/CSS/JS — single file, zero dependencies
- **Audio**: FFmpeg for compression and chunking
- **AI**: OpenAI Whisper (transcription) + GPT (summarization)

---

## Contributing

PRs welcome. The codebase is intentionally small (~400 lines of Python, ~600 lines of frontend) — easy to understand, easy to extend.

```
projectizer/
├── app.py              # Backend — all API logic
├── static/
│   └── index.html      # Frontend — single-page app
├── run.sh              # One-command launcher
├── requirements.txt    # 5 dependencies
└── config.example.json # Config template
```

---

<div align="center">

**Stop paying subscriptions for meeting transcription.**

**Start owning your workflow.**

<br>

MIT License

</div>
