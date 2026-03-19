#!/usr/bin/env bash
# bootstrap.sh — Create and populate the Python virtual environment.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$SCRIPT_DIR/venv"
PYTHON="$VENV/bin/python"

# ── 1. Create virtual environment if missing ───────────────────────────────────
if [[ ! -x "$PYTHON" ]]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV"
fi

# ── 2. Install / update dependencies ──────────────────────────────────────────
echo "Installing / verifying dependencies..."
"$PYTHON" -m pip install --quiet --upgrade pip
"$PYTHON" -m pip install --quiet -r "$SCRIPT_DIR/requirements.txt"

echo "Bootstrap complete. Run ./start.sh to launch the application."
