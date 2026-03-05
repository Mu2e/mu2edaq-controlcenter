"""
status_bar_widget.py - Top-of-window status indicator bar.

Each indicator is a large colored button/label showing a state:
  ok       -> green
  warning  -> yellow/amber
  error    -> red
  unknown  -> grey
"""

from typing import Dict, List

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


STATE_COLORS: Dict[str, str] = {
    "ok":      "#27ae60",   # green
    "warning": "#f39c12",   # amber
    "error":   "#e74c3c",   # red
    "unknown": "#7f8c8d",   # grey
}

STATE_TEXT_COLORS: Dict[str, str] = {
    "ok":      "#ffffff",
    "warning": "#ffffff",
    "error":   "#ffffff",
    "unknown": "#ecf0f1",
}


class IndicatorWidget(QFrame):
    """A single large status indicator."""

    clicked = pyqtSignal(str)  # emits indicator name

    def __init__(self, name: str, state: str = "unknown", parent=None):
        super().__init__(parent)
        self._name = name
        self._state = "unknown"

        self.setFrameShape(QFrame.Shape.Box)
        self.setLineWidth(2)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(64)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(2)

        self._name_label = QLabel(name)
        self._name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = self._name_label.font()
        font.setPointSize(10)
        font.setBold(True)
        self._name_label.setFont(font)

        self._state_label = QLabel("")
        self._state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font2 = self._state_label.font()
        font2.setPointSize(9)
        self._state_label.setFont(font2)

        layout.addWidget(self._name_label)
        layout.addWidget(self._state_label)

        self.set_state(state)

    @property
    def name(self) -> str:
        return self._name

    @property
    def state(self) -> str:
        return self._state

    def set_state(self, state: str, message: str = "") -> None:
        state = state.lower()
        if state not in STATE_COLORS:
            state = "unknown"
        self._state = state
        bg = STATE_COLORS[state]
        fg = STATE_TEXT_COLORS[state]
        self.setStyleSheet(
            f"IndicatorWidget {{ background-color: {bg}; border: 2px solid #2c3e50; border-radius: 4px; }}"
            f"QLabel {{ color: {fg}; background: transparent; }}"
        )
        self._state_label.setText(message if message else state.upper())

    def mousePressEvent(self, event):
        self.clicked.emit(self._name)
        super().mousePressEvent(event)


class StatusBarWidget(QWidget):
    """Horizontal row of status indicators shown at the top of the main window."""

    indicator_clicked = pyqtSignal(str)

    def __init__(self, indicators: List[Dict], parent=None):
        super().__init__(parent)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(4, 4, 4, 4)
        outer.setSpacing(2)

        # Message label (shown when a command sends a message)
        self._msg_label = QLabel("")
        self._msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._msg_label.setWordWrap(True)
        self._msg_label.setStyleSheet(
            "QLabel { color: #ecf0f1; background: #2c3e50; border-radius: 3px; padding: 2px 8px; }"
        )
        self._msg_label.hide()

        row = QHBoxLayout()
        row.setSpacing(6)

        self._indicators: Dict[str, IndicatorWidget] = {}
        for ind in indicators:
            w = IndicatorWidget(ind["name"], ind.get("state", "unknown"))
            w.clicked.connect(self.indicator_clicked)
            self._indicators[ind["name"]] = w
            row.addWidget(w)

        outer.addLayout(row)
        outer.addWidget(self._msg_label)

    def set_indicator_state(self, name: str, state: str, message: str = "") -> None:
        """Update a named indicator's state and optional message text."""
        if name in self._indicators:
            self._indicators[name].set_state(state, message)

    def show_message(self, text: str, level: str = "info") -> None:
        """Display a message below the indicators."""
        level_colors = {
            "info":    ("#2c3e50", "#ecf0f1"),
            "warning": ("#f39c12", "#ffffff"),
            "error":   ("#e74c3c", "#ffffff"),
        }
        bg, fg = level_colors.get(level.lower(), level_colors["info"])
        self._msg_label.setStyleSheet(
            f"QLabel {{ color: {fg}; background: {bg}; border-radius: 3px; padding: 2px 8px; }}"
        )
        self._msg_label.setText(text)
        self._msg_label.show()

    def clear_message(self) -> None:
        self._msg_label.clear()
        self._msg_label.hide()

    def add_indicator(self, name: str, state: str = "unknown") -> None:
        """Dynamically add a new indicator."""
        if name in self._indicators:
            return
        w = IndicatorWidget(name, state)
        w.clicked.connect(self.indicator_clicked)
        self._indicators[name] = w
        self.layout().itemAt(0).layout().addWidget(w)
