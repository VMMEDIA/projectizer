#!/bin/bash
# Projectizer launcher (browser mode).
#
# Self-contained architecture: all runtime files live inside
# Projectizer.app/Contents/Resources/, including the venv. This script:
#   1. Runs pre-flight checks (Python 3.10+, FFmpeg)
#   2. Syncs source files from project root into the .app bundle
#   3. Sets up Resources/.venv if missing or requirements.txt changed
#   4. Launches app.py in browser mode
#
# Edit source files in the project root; this script keeps the .app bundle
# in sync so `open Projectizer.app` always reflects your latest changes.

set -e

cd "$(dirname "$0")"
PROJECT_ROOT="$(pwd)"

# Find Projectizer.app in the standard locations. Priority:
#   1. Project root (default) — the source bundle, recommended for dev
#   2. /Applications/Projectizer.app — for users who moved the .app there
#   3. ~/Applications/Projectizer.app
#   4. PROJECTIZER_APP env var override
#
# This way `bash run.sh` keeps working even if you moved the bundle to
# /Applications. The .app at the resolved location becomes the build target.
find_app() {
    if [ -n "$PROJECTIZER_APP" ] && [ -d "$PROJECTIZER_APP/Contents/Resources" ]; then
        echo "$PROJECTIZER_APP"; return 0
    fi
    for candidate in \
        "$PROJECT_ROOT/Projectizer.app" \
        "/Applications/Projectizer.app" \
        "$HOME/Applications/Projectizer.app"; do
        if [ -d "$candidate/Contents/Resources" ]; then
            echo "$candidate"; return 0
        fi
    done
    return 1
}

if ! APP_PATH=$(find_app); then
    cat <<'EOF' >&2
ERROR: Projectizer.app bundle not found.

Looked in:
  ./Projectizer.app
  /Applications/Projectizer.app
  ~/Applications/Projectizer.app

Either re-clone the repo (which ships with the bundle skeleton) or set
PROJECTIZER_APP=/path/to/Projectizer.app to point to a custom location.
EOF
    exit 1
fi

APP_RES="$APP_PATH/Contents/Resources"
echo "Using bundle: $APP_PATH"

# --- 1. Python 3.10+ -----------------------------------------------------

if ! command -v python3 >/dev/null 2>&1; then
    cat <<'EOF' >&2
ERROR: python3 not found in PATH.

Install Python 3.10 or newer:
  macOS:   brew install python@3.11
  Linux:   sudo apt install python3.11 python3.11-venv     (Debian/Ubuntu)
  Windows: https://www.python.org/downloads/  (check "Add to PATH")
EOF
    exit 1
fi

if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'; then
    PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    cat <<EOF >&2
ERROR: Python 3.10+ required, but you have $PY_VER.

  macOS: brew install python@3.11
  Linux: sudo apt install python3.11 python3.11-venv
EOF
    exit 1
fi

# --- 2. FFmpeg + ffprobe ------------------------------------------------

if ! command -v ffmpeg >/dev/null 2>&1 || ! command -v ffprobe >/dev/null 2>&1; then
    cat <<'EOF' >&2
ERROR: ffmpeg / ffprobe not found in PATH.

Install FFmpeg:
  macOS:   brew install ffmpeg
  Linux:   sudo apt install ffmpeg                  (Debian/Ubuntu)
           sudo dnf install ffmpeg                  (Fedora/RHEL)
  Windows: winget install Gyan.FFmpeg               (or  choco install ffmpeg)

After installing, re-open your terminal so PATH refreshes.
EOF
    exit 1
fi

# --- 3. Sync source files into the .app bundle ---------------------------

echo "Syncing source files into the .app bundle..."
cp app.py launcher.py requirements.txt config.example.json "$APP_RES/"
# Mirror the static dir (rsync-like behavior with cp -R after delete)
rm -rf "$APP_RES/static"
cp -R static "$APP_RES/static"
# Don't overwrite a real config.json that the user may have customized inside
# the bundle — only seed it if missing.
if [ -f config.json ] && [ ! -f "$APP_RES/config.json" ]; then
    cp config.json "$APP_RES/"
fi

# --- 4. Virtualenv inside the bundle ------------------------------------

REQS_HASH=$(python3 -c "import hashlib; print(hashlib.sha1(open('$APP_RES/requirements.txt','rb').read()).hexdigest())")
MARKER="$APP_RES/.venv/.installed"
VENV="$APP_RES/.venv"

if [ ! -d "$VENV" ] || [ "$(cat "$MARKER" 2>/dev/null)" != "$REQS_HASH" ]; then
    if [ ! -d "$VENV" ]; then
        echo "Creating virtual environment in the .app bundle..."
        python3 -m venv "$VENV"
    else
        echo "requirements.txt changed since last install — refreshing dependencies..."
    fi

    # Use python -m pip — pip's shebang has the venv's absolute path baked in,
    # which breaks when the .app bundle is moved.
    echo "Upgrading pip..."
    "$VENV/bin/python" -m pip install --upgrade pip

    echo "Installing dependencies (~30s on first run, ~75 MB on disk)..."
    "$VENV/bin/python" -m pip install -r "$APP_RES/requirements.txt"

    echo "$REQS_HASH" > "$MARKER"
    echo "Setup complete."
fi

# --- 5. Launch ----------------------------------------------------------

echo ""
echo "  ╔══════════════════════════════════════╗"
echo "  ║   Projectizer                        ║"
echo "  ║   http://localhost:${PORT:-8899}              ║"
echo "  ╚══════════════════════════════════════╝"
echo ""

cd "$APP_RES"
exec "$VENV/bin/python" app.py
