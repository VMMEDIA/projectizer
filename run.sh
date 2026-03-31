#!/bin/bash
set -e

cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
    echo "Setting up virtual environment..."
    python3 -m venv .venv
    .venv/bin/pip install -q -r requirements.txt
fi

echo ""
echo "  ╔══════════════════════════════════════╗"
echo "  ║   Projectizer                        ║"
echo "  ║   http://localhost:8899              ║"
echo "  ╚══════════════════════════════════════╝"
echo ""

.venv/bin/python app.py
