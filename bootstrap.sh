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

# ── 3. mu2edaq-discovery (auto-discovery protocol) ────────────────────────────
# Best effort: it is not on PyPI, so it cannot live in requirements.txt.
# Prefer a sibling checkout, fall back to GitHub; the app degrades gracefully
# to no discovery when it is absent.
if ! "$PYTHON" -c 'import mu2edaq_discovery' 2>/dev/null; then
    if [[ -d "$SCRIPT_DIR/../mu2edaq-discovery" ]]; then
        "$PYTHON" -m pip install --quiet -e "$SCRIPT_DIR/../mu2edaq-discovery" \
            && echo "Installed mu2edaq-discovery from sibling checkout"
    else
        "$PYTHON" -m pip install --quiet 'git+https://github.com/Mu2e/mu2edaq-discovery' 2>/dev/null \
            && echo "Installed mu2edaq-discovery from GitHub" \
            || echo "note: mu2edaq-discovery not installed; auto-discovery disabled"
    fi
fi

echo "Bootstrap complete. Run ./start.sh to launch the application."
