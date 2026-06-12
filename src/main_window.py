"""
main_window.py - Main application window for the Control Center.
"""

import datetime
import os
from typing import Dict, Optional

import yaml
from PyQt6.QtCore import QMetaObject, Qt, Q_ARG, QTimer, pyqtSlot
from PyQt6.QtGui import QActionGroup
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from status_bar_widget import StatusBarWidget
from status_server import StatusServer
from stylesheets import STYLESHEETS
from web_grid import WebGrid


class MainWindow(QMainWindow):
    def __init__(self, cfg: Dict, config_path: str):
        super().__init__()
        self._cfg = cfg
        self._config_path = config_path

        self.setWindowTitle(cfg.get("title", "Control Center"))
        self.resize(1280, 900)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        vbox = QVBoxLayout(central)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        # 1. Status indicator bar
        self._status_bar_widget = StatusBarWidget(
            cfg.get("status_indicators", []), parent=self
        )
        vbox.addWidget(self._status_bar_widget)

        # 2. Web grid (must be created before toolbar, which references it)
        grid_cfg = cfg.get("grid", {})
        self._web_grid = WebGrid(
            rows=grid_cfg.get("rows", 2),
            cols=grid_cfg.get("cols", 2),
            pages=cfg.get("pages", []),
        )

        # 3. Grid toolbar (built after _web_grid so it can connect signals)
        vbox.addWidget(self._build_grid_toolbar())

        vbox.addWidget(self._web_grid, stretch=1)

        # Menu bar
        self._build_menu()

        # Qt status bar (bottom)
        self._qt_status = QStatusBar()
        self.setStatusBar(self._qt_status)
        self._qt_status.showMessage("Ready")

        # Clock in the bottom-right corner of the status bar
        self._clock_label = QLabel()
        self._clock_label.setStyleSheet("padding-right: 6px; font-weight: bold;")
        self._qt_status.addPermanentWidget(self._clock_label)
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)
        self._update_clock()

        # Start status command server
        srv_cfg = cfg.get("status_server", {})
        srv_port = int(os.environ.get("CRS_PORT_CMD",
                                      srv_cfg.get("port", 9876)))
        self._server = StatusServer(
            host=srv_cfg.get("host", "127.0.0.1"),
            port=srv_port,
            command_callback=self._handle_command,
        )
        self._server.start()

        # Announce via mu2edaq-discovery once the command server is up.
        # Optional dependency: the app runs normally without it.
        self._responder = None
        try:
            from mu2edaq_discovery import Responder
            self._responder = Responder(
                name="DAQ Control Center", app="controlcenter",
                port=srv_port, scheme="tcp")
            self._responder.start()
        except ImportError:
            pass

    # -------------------------------------------------------------------------
    # Toolbar
    # -------------------------------------------------------------------------

    def _build_grid_toolbar(self) -> QWidget:
        toolbar = QWidget()
        toolbar.setFixedHeight(36)
        toolbar.setStyleSheet("background: #34495e;")
        hbox = QHBoxLayout(toolbar)
        hbox.setContentsMargins(6, 2, 6, 2)
        hbox.setSpacing(8)

        lbl = QLabel("Grid:")
        lbl.setStyleSheet("color: #ecf0f1; font-weight: bold;")
        hbox.addWidget(lbl)

        # Rows spinner
        row_lbl = QLabel("Rows:")
        row_lbl.setStyleSheet("color: #ecf0f1;")
        hbox.addWidget(row_lbl)
        self._row_spin = QSpinBox()
        self._row_spin.setRange(1, 8)
        self._row_spin.setValue(self._cfg.get("grid", {}).get("rows", 2))
        self._row_spin.setFixedWidth(55)
        hbox.addWidget(self._row_spin)

        # Cols spinner
        col_lbl = QLabel("Cols:")
        col_lbl.setStyleSheet("color: #ecf0f1;")
        hbox.addWidget(col_lbl)
        self._col_spin = QSpinBox()
        self._col_spin.setRange(1, 8)
        self._col_spin.setValue(self._cfg.get("grid", {}).get("cols", 2))
        self._col_spin.setFixedWidth(55)
        hbox.addWidget(self._col_spin)

        apply_btn = QPushButton("Apply")
        apply_btn.setFixedWidth(60)
        apply_btn.clicked.connect(self._apply_grid_size)
        hbox.addWidget(apply_btn)

        hbox.addStretch()

        reload_btn = QPushButton("Reload All")
        reload_btn.setFixedWidth(80)
        reload_btn.clicked.connect(self._web_grid.reload_all)
        hbox.addWidget(reload_btn)

        clear_msg_btn = QPushButton("Clear Message")
        clear_msg_btn.setFixedWidth(110)
        clear_msg_btn.clicked.connect(self._status_bar_widget.clear_message)
        hbox.addWidget(clear_msg_btn)

        return toolbar

    def _apply_grid_size(self) -> None:
        rows = self._row_spin.value()
        cols = self._col_spin.value()
        self._web_grid.set_grid_size(rows, cols)

    # -------------------------------------------------------------------------
    # Menu
    # -------------------------------------------------------------------------

    def _build_menu(self) -> None:
        mb = self.menuBar()

        # File menu
        file_menu = mb.addMenu("&File")
        file_menu.addAction("Save Layout...", self._save_layout)
        file_menu.addAction("Load Layout...", self._load_layout)
        file_menu.addSeparator()
        file_menu.addAction("Take Screenshot...", self._take_screenshot)
        file_menu.addSeparator()
        file_menu.addAction("&Quit", self.close)

        # View menu
        view_menu = mb.addMenu("&View")
        view_menu.addAction("Reload All Pages", self._web_grid.reload_all)

        # Style menu
        style_menu = mb.addMenu("&Style")
        style_group = QActionGroup(self)
        style_group.setExclusive(True)
        for name, qss in STYLESHEETS:
            action = style_menu.addAction(name)
            action.setCheckable(True)
            action.setData(qss)
            action.triggered.connect(
                lambda checked, q=qss, n=name: self._apply_stylesheet(q, n)
            )
            style_group.addAction(action)
            if name == "System Default":
                action.setChecked(True)
        self._style_actions = style_group

        # Help menu
        help_menu = mb.addMenu("&Help")
        help_menu.addAction("About", self._show_about)

    def _apply_stylesheet(self, qss: str, name: str) -> None:
        QApplication.instance().setStyleSheet(qss)
        self._qt_status.showMessage(f"Style: {name}")

    def _save_layout(self) -> None:
        """Save the current grid layout to a user-chosen YAML file."""
        default_dir = os.path.dirname(self._config_path)
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Layout",
            default_dir,
            "Layout files (*.yaml *.yml);;All files (*)",
        )
        if not path:
            return

        layout = {
            "grid": {
                "rows": self._web_grid.rows,
                "cols": self._web_grid.cols,
            },
            "pages": self._web_grid.get_pages(),
            "splitter_sizes": self._web_grid.get_splitter_sizes(),
        }
        try:
            with open(path, "w") as fh:
                yaml.dump(layout, fh, default_flow_style=False, sort_keys=False)
            self._qt_status.showMessage(f"Layout saved to {path}")
        except OSError as exc:
            QMessageBox.critical(self, "Save Layout", f"Failed to save: {exc}")

    def _load_layout(self) -> None:
        """Load a previously saved layout file and apply it to the grid."""
        default_dir = os.path.dirname(self._config_path)
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Layout",
            default_dir,
            "Layout files (*.yaml *.yml);;All files (*)",
        )
        if not path:
            return

        try:
            with open(path, "r") as fh:
                layout = yaml.safe_load(fh) or {}
        except (OSError, yaml.YAMLError) as exc:
            QMessageBox.critical(self, "Load Layout", f"Failed to read file:\n{exc}")
            return

        grid = layout.get("grid", {})
        rows = int(grid.get("rows", self._web_grid.rows))
        cols = int(grid.get("cols", self._web_grid.cols))
        pages = layout.get("pages", [])

        self._web_grid.set_grid_size(rows, cols)
        # Re-assign pages explicitly by position
        for page in pages:
            pos = page.get("position")
            if pos:
                self._web_grid.set_cell(
                    pos[0], pos[1], page["name"], page["url"],
                    float(page.get("zoom", 1.0)),
                )

        # Update toolbar spinners to reflect loaded dimensions
        self._row_spin.setValue(rows)
        self._col_spin.setValue(cols)

        # Restore splitter proportions if present
        splitter_sizes = layout.get("splitter_sizes")
        if splitter_sizes:
            self._web_grid.apply_splitter_sizes(splitter_sizes)

        self._qt_status.showMessage(f"Layout loaded from {path}")

    def _take_screenshot(self) -> None:
        """Grab the entire window and save it to a user-chosen image file."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = os.path.join(
            os.path.dirname(self._config_path),
            f"screenshot_{timestamp}.png",
        )
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Screenshot",
            default_name,
            "PNG images (*.png);;JPEG images (*.jpg *.jpeg);;All files (*)",
        )
        if not path:
            return

        screen = QApplication.primaryScreen()
        pixmap = screen.grabWindow(int(self.winId()))
        if pixmap.save(path):
            self._qt_status.showMessage(f"Screenshot saved to {path}")
        else:
            QMessageBox.critical(self, "Screenshot", f"Failed to save image to:\n{path}")

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "About Control Center",
            "<b>Control Center</b><br>"
            "Aggregates and displays web pages in a configurable grid.<br><br>"
            "Status commands are accepted via TCP socket.<br>"
            "See <code>man controlcenter</code> for details.",
        )

    # -------------------------------------------------------------------------
    # Status command handler (called from background thread)
    # -------------------------------------------------------------------------

    def _handle_command(self, cmd: Dict) -> Optional[Dict]:
        """
        Dispatch incoming command dict.
        This is called from the StatusServer thread — use invokeMethod to
        update the GUI safely from the main thread.
        """
        command = cmd.get("command", "")

        if command == "set_status":
            name = cmd.get("indicator", "")
            state = cmd.get("state", "unknown")
            message = cmd.get("message", "")
            QMetaObject.invokeMethod(
                self,
                "_set_indicator",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, name),
                Q_ARG(str, state),
                Q_ARG(str, message),
            )
            return {"status": "ok"}

        elif command == "set_message":
            text = cmd.get("text", "")
            level = cmd.get("level", "info")
            QMetaObject.invokeMethod(
                self,
                "_show_message",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, text),
                Q_ARG(str, level),
            )
            return {"status": "ok"}

        elif command == "clear_message":
            QMetaObject.invokeMethod(
                self,
                "_clear_message",
                Qt.ConnectionType.QueuedConnection,
            )
            return {"status": "ok"}

        elif command == "reload_all":
            QMetaObject.invokeMethod(
                self._web_grid,
                "reload_all",
                Qt.ConnectionType.QueuedConnection,
            )
            return {"status": "ok"}

        elif command == "get_status":
            # Return current indicator states (safe to call cross-thread for reads)
            indicators = {}
            for name, widget in self._status_bar_widget._indicators.items():
                indicators[name] = widget.state
            return {"status": "ok", "indicators": indicators}

        else:
            return {"status": "error", "message": f"Unknown command: {command!r}"}

    @pyqtSlot(str, str, str)
    def _set_indicator(self, name: str, state: str, message: str) -> None:
        self._status_bar_widget.set_indicator_state(name, state, message)
        self._qt_status.showMessage(
            f"Indicator '{name}' set to {state.upper()}"
            + (f": {message}" if message else "")
        )

    @pyqtSlot(str, str)
    def _show_message(self, text: str, level: str) -> None:
        self._status_bar_widget.show_message(text, level)
        self._qt_status.showMessage(f"[{level.upper()}] {text}")

    @pyqtSlot()
    def _clear_message(self) -> None:
        self._status_bar_widget.clear_message()

    # -------------------------------------------------------------------------
    # Cleanup
    # -------------------------------------------------------------------------

    def _update_clock(self) -> None:
        self._clock_label.setText(
            datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        )

    def closeEvent(self, event):
        self._clock_timer.stop()
        if self._responder is not None:
            self._responder.stop()
        self._server.stop()
        super().closeEvent(event)
