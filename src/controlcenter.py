#!/usr/bin/env python3
"""
controlcenter.py - Entry point for the Mu2e DAQ Control Center application.

Usage:
    python controlcenter.py [--config PATH]

See man controlcenter(1) for full documentation.
"""

import argparse
import os
import sys

# Ensure src/ is on the path when invoked directly
_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from PyQt6.QtWidgets import QApplication, QMessageBox

from config_loader import load_config
from main_window import MainWindow


def _default_config_path() -> str:
    repo_root = os.path.dirname(_SRC_DIR)
    return os.path.join(repo_root, "config", "controlcenter.yaml")


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="controlcenter",
        description="Control Center — aggregates and displays web pages in a configurable grid.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  controlcenter
  controlcenter --config /path/to/my_config.yaml

Status commands are sent via TCP to the configured host/port (default 127.0.0.1:9876).
See man controlcenter(1) and man controlcenter-send(1) for details.
""",
    )
    parser.add_argument(
        "--config",
        metavar="PATH",
        default=_default_config_path(),
        help="Path to the YAML configuration file (default: config/controlcenter.yaml)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="controlcenter 1.0.0",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)

    # Must create QApplication before loading any Qt modules that need it
    app = QApplication(sys.argv)
    app.setApplicationName("ControlCenter")
    app.setApplicationVersion("1.0.0")

    # Load configuration
    try:
        cfg = load_config(args.config)
    except FileNotFoundError as exc:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Configuration Error")
        msg.setText(str(exc))
        msg.exec()
        return 1
    except Exception as exc:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Configuration Error")
        msg.setText(f"Failed to parse configuration:\n{exc}")
        msg.exec()
        return 1

    # Control-room port override: CRS_PORT_CMD (exported by crs-app from
    # apps.yaml) takes precedence over status_server.port in the config file.
    _crs_cmd = os.environ.get("CRS_PORT_CMD")
    if _crs_cmd:
        cfg["status_server"]["port"] = int(_crs_cmd)

    window = MainWindow(cfg, config_path=args.config)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
