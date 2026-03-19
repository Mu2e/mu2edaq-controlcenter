# mu2edaq-controlcenter

A PyQt6-based desktop application for the Mu2e DAQ system that aggregates multiple web-based monitoring pages into a single configurable grid GUI, with status indicators and a TCP command interface.

![Control Center Screenshot](screenshot_20260305_165821.png)

## Features

- **Configurable web grid** — display any number of web pages (dashboards, monitors, etc.) in a resizable grid layout
- **Status indicator bar** — color-coded indicators (ok/warning/error/unknown) for named subsystems (DAQ, Trigger, Storage, etc.)
- **Message banner** — display info/warning/error messages across the top of the window
- **Drag-to-swap** — drag cells within the grid to rearrange page positions
- **Save layout** — File → Save Layout writes the current arrangement back to the YAML config
- **Load layout** — File → Load Layout opens a different YAML config without restarting
- **Screenshot** — File → Take Screenshot saves a PNG of the current window
- **Themes** — Style menu offers 9 built-in QSS themes (System Default, Windows Classic, Windows XP, Dark Slate, Light Modern, Midnight Blue, Solarized Dark, High Contrast, Warm Earth)
- **TCP status server** — external processes update indicators and reload pages via a simple JSON protocol
- **IPv4 and IPv6** support

## Requirements

- Python 3.9+
- PyQt6
- PyQt6-WebEngine
- PyYAML

## Installation

Run the bootstrap script once to create the virtual environment and install dependencies:

```bash
./bootstrap.sh
```

## Starting and Stopping

```bash
./start.sh    # launch the application in the background
./stop.sh     # shut it down cleanly
```

`start.sh` activates the virtual environment, launches the app, waits for the TCP status server to be ready, and pings each status indicator. The app's PID is written to `controlcenter.pid` so `stop.sh` can find it.

To use a non-default config file, invoke the app directly:

```bash
source venv/bin/activate
python src/controlcenter.py --config PATH/TO/config.yaml
```

| Option | Default | Description |
|---|---|---|
| `--config PATH` | `config/controlcenter.yaml` | Path to YAML configuration file |
| `--version` | | Print version and exit |

## Configuration

Edit `config/controlcenter.yaml`:

```yaml
title: "Mu2e DAQ Control Center"

grid:
  rows: 2
  cols: 2

status_indicators:
  - name: "DAQ"
    state: unknown        # ok | warning | error | unknown
  - name: "Trigger"
    state: unknown

pages:
  - name: "Dashboard"
    url: "http://localhost:5001"
    position: [0, 0]      # [row, col], zero-indexed; omit to fill automatically
  - name: "Disk Watcher"
    url: "http://localhost:5002"
    position: [0, 1]

status_server:
  host: "127.0.0.1"       # "" or "::" to listen on all interfaces
  port: 9876
```

## TCP Status Server

The Control Center listens for newline-terminated JSON commands over TCP. Use `controlcenter-send` (or any TCP client) to drive it from scripts or other processes.

### Commands

| Command | Fields | Description |
|---|---|---|
| `set_status` | `indicator`, `state`, `message` (opt.) | Set a named indicator's state |
| `set_message` | `level`, `text` | Display a banner (info/warning/error) |
| `clear_message` | — | Clear the banner |
| `reload_all` | — | Reload all embedded web pages |
| `get_status` | — | Return current state of all indicators |
| `ping` | — | Test connectivity |

### `controlcenter-send` CLI

```bash
# Set an indicator
./venv/bin/python src/controlcenter_send.py set-status DAQ ok "All systems nominal"
./venv/bin/python src/controlcenter_send.py set-status Trigger warning "High occupancy"

# Display a message banner
./venv/bin/python src/controlcenter_send.py set-message error "Run aborted by operator"
./venv/bin/python src/controlcenter_send.py clear-message

# Reload all pages
./venv/bin/python src/controlcenter_send.py reload-all

# Query status
./venv/bin/python src/controlcenter_send.py get-status

# Test connectivity
./venv/bin/python src/controlcenter_send.py ping

# Custom host/port
./venv/bin/python src/controlcenter_send.py --host ::1 --port 9876 get-status
```

### Raw JSON example

```bash
echo '{"command":"set_status","indicator":"DAQ","state":"ok"}' | nc 127.0.0.1 9876
```

## Project Structure

```
mu2edaq-controlcenter/
├── config/
│   └── controlcenter.yaml     # Main configuration file
├── man/
│   ├── controlcenter.1        # Man page for controlcenter
│   └── controlcenter-send.1   # Man page for controlcenter-send
├── src/
│   ├── controlcenter.py       # Entry point (argparse, QApplication)
│   ├── main_window.py         # QMainWindow: ties everything together
│   ├── status_bar_widget.py   # Top indicator bar widget
│   ├── web_grid.py            # Grid of web cells, drag-to-swap
│   ├── status_server.py       # TCP server thread
│   ├── config_loader.py       # YAML load and validation
│   ├── stylesheets.py         # Built-in QSS themes
│   └── controlcenter_send.py  # CLI client for sending commands
└── doc/                       # Additional documentation
```

## Man Pages

```bash
man man/controlcenter.1
man man/controlcenter-send.1
```
