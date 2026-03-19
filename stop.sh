#!/usr/bin/env bash
# stop.sh — Shut down a running Control Center instance cleanly.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIDFILE="$SCRIPT_DIR/controlcenter.pid"

# ── 1. Resolve the PID ────────────────────────────────────────────────────────
if [[ -f "$PIDFILE" ]]; then
    PID="$(cat "$PIDFILE")"
else
    # Fall back to searching by process name if the PID file is missing
    PID="$(pgrep -f 'controlcenter.py' | head -1 || true)"
fi

if [[ -z "$PID" ]]; then
    echo "Control Center does not appear to be running."
    exit 0
fi

if ! kill -0 "$PID" 2>/dev/null; then
    echo "No process found with PID $PID — already stopped."
    rm -f "$PIDFILE"
    exit 0
fi

# ── 2. Send SIGTERM and wait for a clean exit ──────────────────────────────────
echo "Stopping Control Center (PID $PID)..."
kill -TERM "$PID"

MAX_WAIT=10
WAITED=0
while kill -0 "$PID" 2>/dev/null; do
    if (( WAITED >= MAX_WAIT )); then
        echo "Process did not exit after ${MAX_WAIT}s — sending SIGKILL..."
        kill -KILL "$PID" 2>/dev/null || true
        break
    fi
    sleep 1
    (( WAITED += 1 ))
done

rm -f "$PIDFILE"
echo "Control Center stopped."
