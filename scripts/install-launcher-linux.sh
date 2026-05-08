#!/bin/bash
# Install a desktop entry so Projectizer appears in your applications menu.
#
# Run this once after you've set up the venv (bash run.sh, or pip install -r requirements.txt).
# It writes ~/.local/share/applications/projectizer.desktop with the absolute
# path to this clone.

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DESKTOP_DIR="$HOME/.local/share/applications"
DESKTOP_FILE="$DESKTOP_DIR/projectizer.desktop"

mkdir -p "$DESKTOP_DIR"
chmod +x "$PROJECT_DIR/scripts/projectizer-launcher.sh"

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=Projectizer
GenericName=Meeting Transcription
Comment=Transcribe and summarize meeting recordings with Whisper
Exec=$PROJECT_DIR/scripts/projectizer-launcher.sh
Path=$PROJECT_DIR
Terminal=false
Categories=AudioVideo;Audio;Office;
StartupWMClass=Projectizer
Keywords=transcription;whisper;meeting;summary;
EOF

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$DESKTOP_DIR" >/dev/null 2>&1 || true
fi

echo "Installed: $DESKTOP_FILE"
echo "Project dir: $PROJECT_DIR"
echo
echo "Projectizer should now appear in your applications menu."
echo "If pywebview is missing system deps, install on Debian/Ubuntu:"
echo "  sudo apt install python3-gi gir1.2-webkit2-4.1 libwebkit2gtk-4.1-0"
echo "  source $PROJECT_DIR/.venv/bin/activate && pip install 'pywebview[gtk]'"
