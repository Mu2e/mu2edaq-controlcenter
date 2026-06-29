#!/usr/bin/env bash
# start-mu2edaq-controlcenter.sh — standardized Mu2e control-room start script.
# Activates the virtual environment and launches the Control Center. Launched
# by the control room as `crs-app start controlcenter`, which exports
# CRS_PORT_CMD from apps.yaml; controlcenter.py honors it as the status-server
# port (overriding status_server.port in the config). Default 9876.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$SCRIPT_DIR/venv"
PYTHON="$VENV/bin/python"
SEND="$SCRIPT_DIR/src/controlcenter_send.py"
CONFIG="$SCRIPT_DIR/config/controlcenter.yaml"
PIDFILE="$SCRIPT_DIR/controlcenter.pid"
export CRS_PORT_CMD="${CRS_PORT_CMD:-9876}"

# ── 1. Verify the virtual environment exists ───────────────────────────────────
if [[ ! -x "$PYTHON" ]]; then
    echo "ERROR: virtual environment not found. Run ./bootstrap.sh first." >&2
    exit 1
fi

source "$VENV/bin/activate"

# ── 2. Launch the application in the background ────────────────────────────────
echo "Starting Control Center..."
python "$SCRIPT_DIR/src/controlcenter.py" --config "$CONFIG" &
APP_PID=$!
echo "$APP_PID" > "$PIDFILE"
echo "  PID: $APP_PID"

# ── 3. Wait for the status server to accept connections ────────────────────────
HOST="127.0.0.1"
PORT="$CRS_PORT_CMD"
MAX_WAIT=15   # seconds
WAITED=0

echo "Waiting for status server on $HOST:$PORT..."
until python -c "
import socket, sys
try:
    s = socket.create_connection(('$HOST', $PORT), timeout=1)
    s.close()
    sys.exit(0)
except OSError:
    sys.exit(1)
" 2>/dev/null; do
    if (( WAITED >= MAX_WAIT )); then
        echo "ERROR: status server did not start within ${MAX_WAIT}s" >&2
        kill "$APP_PID" 2>/dev/null || true
        exit 1
    fi
    sleep 1
    (( WAITED += 1 ))
done
echo "  Server ready (${WAITED}s)."

# ── 4. Ping each status indicator ─────────────────────────────────────────────
INDICATORS=("DAQ" "Trigger" "Misc" "Storage")

echo "Pinging status indicators..."
for indicator in "${INDICATORS[@]}"; do
    echo -n "  $indicator: "
    python "$SEND" ping && echo "ok" || echo "FAILED"
done

echo "Control Center is running (PID $APP_PID)."
