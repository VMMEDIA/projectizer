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

<sub>🇬🇧 English · <a href="README.it.md">🇮🇹 Italiano</a></sub>

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
| **Speaker labels** | Limited | Built-in diarization via OpenAI |

<br>

> **Record with whatever you already have.** Drop the files into Projectizer. Get your summary. Done.

---

## What You Get

**Transcription** — Whisper-powered, supports 50+ languages with auto-detection. Upload one file or ten — Projectizer concatenates, compresses, and chunks them automatically.

**Speaker Diarization (optional)** — Identify who said what via OpenAI's `gpt-4o-transcribe-diarize`. Get transcripts labeled `Persona 1: …`, `Persona 2: …` instead of a wall of text. Toggle on in the UI — no extra service, no extra dependency.

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

The script syncs source files into `Projectizer.app/Contents/Resources/`, creates a virtual environment **inside the bundle**, installs dependencies, and starts the server at **http://localhost:8899**.

Paste your OpenAI API key in the **Settings** panel and you're ready to go.

> **First run takes ~30 seconds** — the bundle ships with a slim Python stack (~75 MB). Subsequent runs start instantly.

### Two ways to run

| Mode | How | Result |
|------|-----|--------|
| **Browser** (development) | `bash run.sh` | Opens at `localhost:8899` in your default browser. Auto-syncs source edits into the .app bundle. |
| **Native window** (macOS) | `open Projectizer.app` | Real desktop app with its own icon and window. The bundle is **self-contained** — drop it in `/Applications/`, `~/Desktop/`, anywhere. See [Run as a native app](#run-as-a-native-app). |

Both modes share the same backend; pick whichever feels more natural.

---

## Installation

### 1. System Prerequisites

You need three things on your machine before cloning the repo:

#### Python 3.10 or newer

Check your version:

```bash
python3 --version
```

| Platform | Install |
|----------|---------|
| **macOS** | `brew install python@3.11` |
| **Ubuntu / Debian** | `sudo apt install python3.11 python3.11-venv` |
| **Fedora / RHEL** | `sudo dnf install python3.11` |
| **Windows** | [python.org installer](https://www.python.org/downloads/) — check "Add to PATH" |

> Projectizer is tested on 3.10, 3.11, 3.12, and 3.13.

#### FFmpeg

Used for audio compression, concatenation, and probing.

| Platform | Install |
|----------|---------|
| **macOS** | `brew install ffmpeg` |
| **Ubuntu / Debian** | `sudo apt install ffmpeg` |
| **Fedora / RHEL** | `sudo dnf install ffmpeg` |
| **Windows** | `winget install Gyan.FFmpeg` or `choco install ffmpeg` |

Verify with `ffmpeg -version` and `ffprobe -version` — both must be in your `PATH`.

#### An OpenAI API key

Generate one at [platform.openai.com/api-keys](https://platform.openai.com/api-keys). You'll paste it into the Projectizer Settings panel after first launch — no environment variable needed.

---

### 2. Install Projectizer

#### Option A — Automated (recommended)

```bash
git clone https://github.com/VMMEDIA/projectizer.git
cd projectizer
bash run.sh
```

`run.sh` handles venv creation, `pip install`, and launches the server.

> If you change `requirements.txt` later, delete `.venv/` and re-run `bash run.sh` — the script only installs dependencies on the first run.

#### Option B — Manual

If you want to understand each step or run inside an existing Python environment, the venv is created **inside the .app bundle** so the .app stays portable. Source files are copied in as well:

```bash
git clone https://github.com/VMMEDIA/projectizer.git
cd projectizer

APP_RES=Projectizer.app/Contents/Resources
cp app.py launcher.py requirements.txt config.example.json "$APP_RES/"
cp -R static "$APP_RES/static"

python3 -m venv "$APP_RES/.venv"
"$APP_RES/.venv/bin/python" -m pip install --upgrade pip
"$APP_RES/.venv/bin/python" -m pip install -r "$APP_RES/requirements.txt"

# Browser mode
( cd "$APP_RES" && "$APP_RES/.venv/bin/python" app.py )

# Native window mode
( cd /tmp && "$APP_RES/.venv/bin/python" "$APP_RES/launcher.py" )
```

Once set up, `Projectizer.app` works from Finder too. `bash run.sh` does all of the above for you.

---

### 3. Speaker Diarization (optional)

#### What is diarization?

Diarization figures out **who is speaking when**. Without it, you get one continuous transcript:

```
Okay so the deadline is Friday. I think we should push it to next week.
Why? Because the design isn't ready. Fair enough, let's do Tuesday.
```

With diarization on, you get speaker labels:

```
Persona 1: Okay so the deadline is Friday.
Persona 2: I think we should push it to next week.
Persona 1: Why?
Persona 2: Because the design isn't ready.
Persona 1: Fair enough, let's do Tuesday.
```

#### How it works

Projectizer uses OpenAI's [`gpt-4o-transcribe-diarize`](https://developers.openai.com/api/docs/models/gpt-4o-transcribe-diarize) model, which returns transcription **and** speaker segments in a single API call. No extra service, no extra setup, no extra dependency — just toggle "Identifica parlanti" in the UI.

| Mode | Model | Cost (approx) |
|------|-------|---------------|
| Diarization OFF | `whisper-1` | $0.006/min ($0.36/hour) |
| Diarization ON  | `gpt-4o-transcribe-diarize` | ~$0.025/min (~$1.50/hour) |

> **Note**: With diarization on, the audio still goes to OpenAI like any other transcription. Speaker labels are produced acoustically by their model, no privacy difference vs. plain Whisper.

---

## Configuration

Configuration lives in `Projectizer.app/Contents/Resources/config.json` — **inside the .app bundle**, so it travels with the .app when you move it. The file is created automatically the first time you save settings from the UI. You can also bootstrap it from the template:

```bash
cp config.example.json Projectizer.app/Contents/Resources/config.json
```

```json
{
  "openai_api_key": "sk-...",
  "summary_model": "gpt-4o-mini"
}
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `openai_api_key` | — | Your OpenAI API key (required) |
| `summary_model` | `gpt-4o-mini` | Model for summary generation — swap in `gpt-4o` for higher quality |
| `PORT` (env var) | `8899` | Server port — `PORT=9000 bash run.sh` |

---

## Run as a native app

Want Projectizer to feel like a real desktop application — its own icon, its own window, no browser tab? Use one of the platform launchers below. They all start the server in the background and open the UI in a native window via [pywebview](https://pywebview.flowrl.com/).

> The classic `bash run.sh` flow keeps working unchanged — it auto-syncs your source edits into the bundle, so the `.app` always reflects your latest code.

### macOS — self-contained .app

`Projectizer.app` is **self-contained**: after the first `bash run.sh`, all source files, the Python virtual environment, and dependencies live inside `Projectizer.app/Contents/Resources/`. You can move the `.app` anywhere — `/Applications/`, `~/Desktop/`, an external drive — and it keeps working.

**First-time setup**:

```bash
git clone https://github.com/VMMEDIA/projectizer.git
cd projectizer
bash run.sh
```

This script creates the venv inside the bundle (`Projectizer.app/Contents/Resources/.venv/`, ~75 MB) and starts the browser-mode server. After it boots, you can:

- Stop with `Ctrl+C` and **double-click `Projectizer.app`** to open the native window
- Or just keep using the browser at `localhost:8899`

**Move the `.app` anywhere**:

```bash
# Copy or move it — both work
cp -R Projectizer.app /Applications/
# or
mv Projectizer.app ~/Desktop/Projectizer.app
```

Double-click from the new location. No reconfiguration needed.

> **Architecture note**: Source files live at the project root for editing. `bash run.sh` syncs them into `Projectizer.app/Contents/Resources/` at every run, so edits propagate automatically. The `.app` reads from inside its bundle at runtime, which is why it works after being moved.

> **macOS sandbox / TCC**: When the `.app` is in `~/Documents/`, `~/Desktop/`, `~/Downloads/`, or iCloud Drive, macOS still allows it to read its own bundle contents. Source-tree files outside the bundle are not accessible from a Finder-launched `.app` in those folders — but since everything the runtime needs is *inside* the bundle, this isn't a problem.

> **Custom icon**: Drop an `icon.icns` file into `Projectizer.app/Contents/Resources/` to replace the default. macOS may require you to clear the icon cache (`killall Dock`) to pick it up.

### Windows

```cmd
git clone https://github.com/VMMEDIA/projectizer.git
cd projectizer
Projectizer.bat
```

First run installs the venv, subsequent runs go straight to the native window. Right-click `Projectizer.bat` → **Create shortcut**, then drag the shortcut to the Desktop or pin it to Start.

The launcher uses `pythonw.exe`, so no console window stays open. If something breaks and you want to see logs, edit `Projectizer.bat` and replace `pythonw.exe` with `python.exe`.

### Linux

pywebview on Linux needs system-level GTK + WebKit2GTK packages. On Debian/Ubuntu:

```bash
sudo apt install python3-gi gir1.2-webkit2-4.1 libwebkit2gtk-4.1-0
```

Then set up the venv (one time) and install the desktop entry:

```bash
bash run.sh                                  # ctrl-C once it boots, just to create .venv
source .venv/bin/activate
pip install 'pywebview[gtk]'                 # GTK backend bindings
deactivate

bash scripts/install-launcher-linux.sh
```

The install script writes `~/.local/share/applications/projectizer.desktop` with the absolute path to your clone. Projectizer should now appear in your apps menu.

---

## Troubleshooting

**`ffmpeg: command not found`**
FFmpeg isn't in your `PATH`. On macOS check `brew --prefix`/bin is in `PATH`; on Windows, restart the terminal after install or add the FFmpeg `bin/` folder to PATH manually.

**`ERROR: Could not find a version that satisfies the requirement torch`**
You're likely on Python 3.13 or an unsupported architecture. Install Python 3.11 and recreate `.venv`.

**Diarization fails**
Check your OpenAI API key tier — `gpt-4o-transcribe-diarize` requires the same access as Whisper. If your key works for transcription but the diarize toggle fails, try [platform.openai.com/account/limits](https://platform.openai.com/account/limits).

**Diarization is more expensive than expected**
Diarize mode uses `gpt-4o-transcribe-diarize` (token-billed, ~$0.025/min) instead of `whisper-1` (~$0.006/min). For monologues or single-speaker recordings, leave the toggle off to save money.

**`OSError: [Errno 48] Address already in use`**
Port 8899 is taken. Run with a different port: `PORT=9000 bash run.sh`.

**`run.sh` doesn't pick up new requirements**
`run.sh` auto-detects changes via a SHA-1 hash of `requirements.txt` (stored in `.venv/.installed`). If a refresh fails, force-reinstall by deleting the venv inside the bundle: `rm -rf Projectizer.app/Contents/Resources/.venv && bash run.sh`.

**`Projectizer.app` doesn't open a window**
First, run `bash run.sh` once — it bootstraps the bundle (syncs source files, creates the venv inside `Contents/Resources/`). After that, double-click works. If the `.app` is launched and silently exits, check `/tmp/projectizer-launcher.log` for diagnostics.

**Edits to `app.py` or `static/index.html` don't show up in `Projectizer.app`**
The `.app` reads from `Contents/Resources/`. Run `bash run.sh` to re-sync your edits into the bundle, then re-open the `.app`. (`run.sh` does this every time it starts.)

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

**Smart compression** converts any audio format to Opus 32kbps mono before sending to the API, cutting upload size by 80–90% with zero quality loss for speech.

**Chunking** splits files that exceed Whisper's 25 MB limit, transcribes each segment, and stitches the results seamlessly.

**Diarization (optional)** uses OpenAI's `gpt-4o-transcribe-diarize` model — single API call returns both transcript and speaker-labeled segments. No local ML stack required.

---

## Cost Breakdown

| What | Cost |
|------|------|
| Transcription (`whisper-1`) | $0.006 / minute |
| Transcription + speakers (`gpt-4o-transcribe-diarize`) | ~$0.025 / minute |
| Summary (`gpt-4o-mini`) | ~$0.0003 / meeting |
| **1-hour meeting, transcribe only** | **~$0.36** |
| **1-hour meeting, with diarization** | **~$1.50** |

For context: 200 one-hour meetings per year costs about **$72** without diarization, or **$300** with — still less than one year of Plaud's subscription, no hardware purchase.

---

## Tech Stack

Intentionally minimal. No build step, no bundler, no framework overhead.

- **Backend**: FastAPI + Uvicorn
- **Frontend**: Vanilla HTML/CSS/JS — single file, zero dependencies
- **Audio**: FFmpeg for compression and chunking
- **AI**: OpenAI Whisper (transcription) + GPT-4o-mini (summarization) + `gpt-4o-transcribe-diarize` (optional speaker labels)

---

## Contributing

PRs welcome. The codebase is intentionally small (~500 lines of Python, ~600 lines of frontend) — easy to understand, easy to extend.

```
projectizer/                          (project root — edit source here)
├── app.py                            # Backend — all API logic
├── launcher.py                       # Native-window entry point (pywebview)
├── static/
│   └── index.html                    # Frontend — single-page app
├── run.sh                            # Browser launcher + bundle sync
├── Projectizer.bat                   # Windows launcher → native window
├── scripts/
│   ├── projectizer-launcher.sh       # called by Linux .desktop
│   └── install-launcher-linux.sh     # creates the .desktop entry
├── requirements.txt                  # Python dependencies
├── config.example.json               # Config template
└── Projectizer.app/                  # Self-contained macOS bundle
    └── Contents/
        ├── Info.plist
        ├── MacOS/projectizer         # Bash launcher script
        └── Resources/                # ← runtime files live here
            ├── app.py                # Synced from project root
            ├── launcher.py           #   "
            ├── static/               #   "
            ├── requirements.txt      #   "
            ├── config.json           # User's saved API keys
            └── .venv/                # Python venv (~75 MB, created on first run)
```

**Source of truth**: edit files at the project root. `bash run.sh` keeps `Projectizer.app/Contents/Resources/` in sync — `app.py`, `launcher.py`, `static/`, `requirements.txt`, `config.example.json` are copied into the bundle on every run. The `.venv` and `config.json` (user data) live only inside the bundle.

---

<div align="center">

**Stop paying subscriptions for meeting transcription.**

**Start owning your workflow.**

<br>

MIT License

</div>
