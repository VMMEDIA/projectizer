#!/bin/bash
# Wrapper called by projectizer.desktop. Don't run this directly — use
# scripts/install-launcher-linux.sh once, then launch Projectizer from
# your applications menu.

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

if [ ! -d ".venv" ]; then
    MSG="Projectizer needs to be set up first. Open a terminal in $PROJECT_DIR and run: bash run.sh"
    if command -v notify-send >/dev/null 2>&1; then
        notify-send "Projectizer" "$MSG"
    fi
    echo "$MSG" >&2
    exit 1
fi

exec .venv/bin/python launcher.py
