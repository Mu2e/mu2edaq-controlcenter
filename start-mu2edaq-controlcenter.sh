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

# ── 2. Detect GPU/OpenGL support ────────────────────────────────────────────────
# QWebEngineView (Chromium) needs a working GPU/GLX context. On displays
# without one (e.g. plain X11 forwarding with no direct rendering), Qt's
# hardware compositor eventually aborts the process — but not necessarily
# right away; failure can be delayed well past startup, so detecting it by
# watching the running app (crash window, health checks) is unreliable.
# Instead we probe with a minimal, fast, isolated Qt OpenGL context creation
# attempt before ever launching the full app: the same underlying failure
# ("No matching fbConfigs or visuals found") shows up immediately and
# deterministically at that level.
GPU_PROBE_TIMEOUT=10
echo "Checking for GPU/OpenGL support..."
if timeout "$GPU_PROBE_TIMEOUT" python - <<'PY' >/dev/null 2>&1
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QOpenGLContext, QOffscreenSurface

app = QApplication(sys.argv)
surface = QOffscreenSurface()
surface.create()
ctx = QOpenGLContext()
ok = ctx.create() and ctx.makeCurrent(surface)
sys.exit(0 if ok else 1)
PY
then
    echo "  GPU/OpenGL context OK; using hardware-accelerated rendering."
else
    echo "  No usable GPU/OpenGL context detected; forcing software rendering."
    export QT_QUICK_BACKEND=software
    export QTWEBENGINE_CHROMIUM_FLAGS="--disable-gpu --enable-unsafe-swiftshader"
fi

# ── 3. Launch the application in the background ────────────────────────────────
echo "Starting Control Center..."
python "$SCRIPT_DIR/src/controlcenter.py" --config "$CONFIG" &
APP_PID=$!
echo "$APP_PID" > "$PIDFILE"
echo "  PID: $APP_PID"

# ── 4. Wait for the status server to accept connections ────────────────────────
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
    kill -0 "$APP_PID" 2>/dev/null || { echo "ERROR: process died while waiting for status server" >&2; exit 1; }
    if (( WAITED >= MAX_WAIT )); then
        echo "ERROR: status server did not start within ${MAX_WAIT}s" >&2
        kill "$APP_PID" 2>/dev/null || true
        exit 1
    fi
    sleep 1
    (( WAITED += 1 ))
done
echo "  Server ready (${WAITED}s)."

# ── 5. Ping each status indicator ─────────────────────────────────────────────
INDICATORS=("DAQ" "Trigger" "Misc" "Storage")

echo "Pinging status indicators..."
for indicator in "${INDICATORS[@]}"; do
    echo -n "  $indicator: "
    if kill -0 "$APP_PID" 2>/dev/null && python "$SEND" ping; then
        echo "ok"
    else
        echo "FAILED"
    fi
done

kill -0 "$APP_PID" 2>/dev/null || { echo "ERROR: process died during startup" >&2; exit 1; }
echo "Control Center is running (PID $APP_PID)."
