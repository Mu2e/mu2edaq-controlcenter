# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**mu2edaq-controlcenter** is a PyQt6 desktop application for the Mu2e DAQ (Data Acquisition) system. It aggregates multiple web-based monitoring pages into a configurable grid GUI with color-coded status indicators, a message banner, and a TCP status server for external control.

## Setup and Running

```bash
# Initial setup: create venv and install dependencies
python3 -m venv venv
./venv/bin/pip install PyQt6 PyQt6-WebEngine PyYAML

# Run the application
./venv/bin/python src/controlcenter.py [--config PATH]
# Default config: config/controlcenter.yaml

# Or use the startup script (creates venv, installs deps, launches, and health-checks)
./start.sh
```

## External Control (TCP Client)

```bash
./venv/bin/python src/controlcenter_send.py <command> [args]
# Commands: set-status, set-message, clear-message, reload-all, get-status, ping
# Example: set-status DAQ ok
# Example: set-message warning "Subsystem degraded"
```

## Architecture

The app is split into focused modules under `src/`:

- **`controlcenter.py`** — Entry point; parses args, creates `QApplication`, launches `MainWindow`
- **`main_window.py`** — Orchestrates all UI: loads config, creates `WebGrid`, `StatusBarWidget`, `StatusServer`, handles menu actions and layout persistence
- **`web_grid.py`** — Grid of embedded web views (`QWebEngineView`) with drag-to-swap cells, per-cell zoom, and splitter-based resizing
- **`status_bar_widget.py`** — Color-coded indicator bar; states are `ok | warning | error | unknown`
- **`status_server.py`** — TCP daemon thread receiving newline-delimited JSON commands; emits Qt signals back to the UI thread
- **`config_loader.py`** — Loads and validates YAML config
- **`controlcenter_send.py`** — Standalone CLI that sends JSON commands over TCP to the running app
- **`stylesheets.py`** — Nine built-in QSS themes applied via the View menu

**Threading model**: The TCP server runs on a daemon thread and communicates back to the main (GUI) thread via Qt signals. All UI updates must happen on the main thread.

## Configuration Schema

```yaml
title: "Mu2e DAQ Control Center"
grid:
  rows: 2
  cols: 2
status_indicators:
  - name: "DAQ"
    state: unknown          # ok | warning | error | unknown
pages:
  - name: "Dashboard"
    url: "http://localhost:5001"
    position: [0, 0]        # optional [row, col]
status_server:
  host: "127.0.0.1"         # IPv4 or IPv6 address
  port: 9876
```

Layout state (splitter sizes, zoom levels) is persisted back into the config file on exit.

## No Tests or Linting Configured

There is no test suite or linter configured. Manual testing uses the sample configs in `config/` (`base.yaml`, `testconfig.yaml`, `testconfig-2.yaml`, `testconfig-3.yaml`).
