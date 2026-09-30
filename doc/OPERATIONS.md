---
title: mu2edaq-controlcenter operations
group: control-room
tier: A
audience: shifter
summary: >
  Starting, stopping, checking and troubleshooting the Control Center
  kiosk on the control-room shift-main session
---

# mu2edaq-controlcenter — operations

Runs on the `shift-main` VNC session (`../mu2edaq-controlroom-setup/config/apps.yaml:24`).
It is a GUI: it needs a `DISPLAY`, which on a DAQ host means it must be
started from inside the VNC session, not from a plain ssh login.

## Start and stop

```bash
# control room (assigns CRS_PORT_CMD from the inventory)
crs-app start controlcenter
crs-app stop controlcenter

# local desktop install
mu2edaq-app start controlcenter
mu2edaq-app status controlcenter

# directly, from the checkout
./start-mu2edaq-controlcenter.sh
./stop-mu2edaq-controlcenter.sh
```

`start.sh`/`stop.sh` are symlinks to the long names and behave
identically. Prefer the long names.

First run on a new host needs `./bootstrap.sh` — the start script
refuses to run without `venv/bin/python` and says so.

## What a healthy start looks like

```
Checking for GPU/OpenGL support...
  GPU/OpenGL context OK; using hardware-accelerated rendering.
Starting Control Center...
  PID: 24317
Waiting for status server on 127.0.0.1:9876...
  Server ready (2s).
Pinging status indicators...
  DAQ: ok
  ...
Control Center is running (PID 24317).
```

The script exits non-zero and kills the process if the status server
does not accept a connection within 15 s, so a silent half-start is not
a failure mode here.

Two caveats on that health check:

- The four "indicator" pings are all the same `ping`. They prove the
  socket is up once, not that each indicator exists. A `ping` is
  answered by the server thread without reaching the GUI
  (`src/status_server.py:120`), so a wedged event loop still passes.
- A failed *bind* does not fail the start. `StatusServer.run` prints
  `Failed to bind ...` and returns (`status_server.py:65-67`); the GUI
  stays up. The readiness loop then times out and kills the app, which
  is the right outcome — but if the port is held by something that
  accepts connections, the check passes against the wrong process.

## Checking state

```bash
controlcenter-send ping
controlcenter-send get-status
```

`get-status` is the only command that reports real UI state. Use it,
not `ping`, to confirm the display is actually live.

```bash
mu2edaq-app status controlcenter     # TCP connect on the cmd port
```

## Driving the display

```bash
controlcenter-send set-status DAQ ok "All systems nominal"
controlcenter-send set-status Trigger warning "High occupancy"
controlcenter-send set-message error "Run aborted by operator"
controlcenter-send clear-message
controlcenter-send reload-all          # after restarting a dashboard behind a cell
```

The indicator names must match `status_indicators` in the config —
shipped set: `DAQ`, `Trigger`, `Misc`, `Storage`
(`config/controlcenter.yaml:14-22`). **A misspelled name returns
`{"status": "ok"}` and does nothing.** If a `set-status` appeared to
succeed but the wall display did not change, check the spelling with
`get-status` first; that is the single most common failure report for
this package.

## Troubleshooting

### Grid cells are blank or show a connection error

The cell is a browser pointed at another package's port. The Control
Center is fine; the service behind the cell is not.

| Cell | Service | Port |
|---|---|---|
| Dashboard | `mu2edaq-dashboard` | 5001 |
| Disk Watcher | `mu2edaq-diskwatcher` | 5002 |
| Heart Beats | `mu2edaq-heartbeatmonitor` | 8081 |
| FTS | `mu2edaq-fts` | 5003 |

```bash
mu2edaq-app status                 # all apps at once
curl -sS -o /dev/null -w '%{http_code}\n' http://localhost:5002
```

Restart the offending service, then `controlcenter-send reload-all`.
The URLs are `localhost`, so all four must run on the same host as the
kiosk.

### The app aborts shortly after start, or the window is black

Chromium needs a GL context. The start script probes for one and falls
back to software rendering, printing:

```
  No usable GPU/OpenGL context detected; forcing software rendering.
```

If it aborts anyway, the probe passed but the real context failed.
Force software rendering by hand:

```bash
export QT_QUICK_BACKEND=software
export QTWEBENGINE_CHROMIUM_FLAGS="--disable-gpu --enable-unsafe-swiftshader"
./start-mu2edaq-controlcenter.sh
```

This is the expected path over plain X11 forwarding with no direct
rendering.

### `could not connect to 127.0.0.1:9876`

The app is not running, or the status server failed to bind and the GUI
stayed up without it.

```bash
pgrep -af controlcenter.py
ss -ltnp | grep 9876        # or: lsof -nP -iTCP:9876 -sTCP:LISTEN
```

A bind failure prints `[StatusServer] Failed to bind 127.0.0.1:9876`
on the app's stdout. Port 9876 is the Control Center's alone in both
`apps.yaml` copies, so a clash means a stale instance — find it with
`pgrep` and stop it.

### Stop did not stop it

With no `controlcenter.pid`, the stop script falls back to
`pgrep -f controlcenter.py | head -1`
(`stop-mu2edaq-controlcenter.sh:14`) and may pick the wrong process —
another checkout, or an editor with the filename in its command line.
Check before escalating:

```bash
pgrep -af controlcenter.py
kill -TERM <pid>            # SIGKILL after 10s is what the script does
```

The stop script exits `0` when nothing is running, so a `0` from it is
not evidence that a process was stopped.

## Files and ports

| | |
|---|---|
| Config | `config/controlcenter.yaml` |
| PID file | `controlcenter.pid` |
| Port | 9876/tcp, loopback, `CRS_PORT_CMD` |
| Venv | `venv/` (via `bootstrap.sh`) |
| Logs | none — stdout only; the start script does not redirect it |

There is no log file. Under `crs-app` on a VNC session, stdout goes to
the session's terminal and is lost when it closes. For a persistent
record, redirect by hand.

## Layout persistence

Splitter sizes and per-cell zoom are saved with **File → Save Layout**
to a file the operator names, and restored with the matching load
action (`src/main_window.py:164`, `:199-241`). They are not saved
automatically on exit — closing the kiosk discards an unsaved rearrange.
`CLAUDE.md` says otherwise and is wrong (finding CC-006).
