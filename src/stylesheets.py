"""
stylesheets.py - Built-in QSS stylesheets for the Control Center.

Each entry in STYLESHEETS is (display_name, qss_string).
An empty qss_string means "use the platform default style".
"""

from typing import List, Tuple

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _scrollbar(track: str, handle: str, handle_hover: str, border: str) -> str:
    return f"""
QScrollBar:vertical {{
    background: {track}; width: 12px; margin: 0px;
}}
QScrollBar::handle:vertical {{
    background: {handle}; min-height: 20px; border-radius: 4px;
    border: 1px solid {border};
}}
QScrollBar::handle:vertical:hover {{ background: {handle_hover}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
QScrollBar:horizontal {{
    background: {track}; height: 12px; margin: 0px;
}}
QScrollBar::handle:horizontal {{
    background: {handle}; min-width: 20px; border-radius: 4px;
    border: 1px solid {border};
}}
QScrollBar::handle:horizontal:hover {{ background: {handle_hover}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0px; }}
QScrollBar::corner {{ background: {track}; }}
"""


# ---------------------------------------------------------------------------
# 1. System Default
# ---------------------------------------------------------------------------
_SYSTEM_DEFAULT = ""


# ---------------------------------------------------------------------------
# 2. Windows Classic  (raised/sunken borders, silver palette)
# ---------------------------------------------------------------------------
_WINDOWS_CLASSIC = """
QWidget {
    background-color: #d4d0c8;
    color: #000000;
    font-family: "MS Sans Serif", "Tahoma", sans-serif;
    font-size: 9pt;
}
QMainWindow, QDialog {
    background-color: #d4d0c8;
}
QMenuBar {
    background-color: #d4d0c8;
    border-bottom: 1px solid #808080;
}
QMenuBar::item:selected {
    background-color: #000080;
    color: #ffffff;
}
QMenu {
    background-color: #d4d0c8;
    border: 2px solid;
    border-color: #ffffff #808080 #808080 #ffffff;
}
QMenu::item:selected {
    background-color: #000080;
    color: #ffffff;
}
QPushButton {
    background-color: #d4d0c8;
    border: 2px solid;
    border-color: #ffffff #808080 #808080 #ffffff;
    padding: 3px 8px;
    min-width: 50px;
}
QPushButton:pressed {
    border-color: #808080 #ffffff #ffffff #808080;
}
QPushButton:hover {
    background-color: #e0ddd5;
}
QSpinBox, QLineEdit, QComboBox {
    background-color: #ffffff;
    border: 2px solid;
    border-color: #808080 #ffffff #ffffff #808080;
    padding: 1px 3px;
}
QLabel { background: transparent; }
QStatusBar {
    background-color: #d4d0c8;
    border-top: 1px solid #808080;
}
QSplitter::handle {
    background-color: #d4d0c8;
    border: 1px solid #808080;
}
QSplitter::handle:horizontal { width: 4px; }
QSplitter::handle:vertical   { height: 4px; }
QFrame[frameShape="4"], QFrame[frameShape="5"] {
    border: 2px solid;
    border-color: #808080 #ffffff #ffffff #808080;
}
""" + _scrollbar("#d4d0c8", "#a09890", "#c0b8b0", "#808080")


# ---------------------------------------------------------------------------
# 3. Windows XP Luna  (blue title/menu bar, silver widgets)
# ---------------------------------------------------------------------------
_WINDOWS_XP = """
QWidget {
    background-color: #ece9d8;
    color: #000000;
    font-family: "Tahoma", sans-serif;
    font-size: 9pt;
}
QMainWindow { background-color: #ece9d8; }
QMenuBar {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #4a7bbf, stop:1 #2a5ba0);
    color: #ffffff;
    font-weight: bold;
    padding: 2px;
}
QMenuBar::item { background: transparent; padding: 2px 8px; }
QMenuBar::item:selected {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #6fa0e0, stop:1 #4a7bbf);
    border-radius: 2px;
}
QMenu {
    background-color: #ffffff;
    border: 1px solid #7f9db9;
}
QMenu::item { padding: 3px 20px; }
QMenu::item:selected { background-color: #316ac5; color: #ffffff; }
QPushButton {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #f5f4f0, stop:1 #dddbd2);
    border: 1px solid #7f9db9;
    border-radius: 3px;
    padding: 3px 10px;
    color: #000000;
}
QPushButton:hover {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #fafaf6, stop:1 #eae8e0);
    border-color: #316ac5;
}
QPushButton:pressed {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #dddbd2, stop:1 #f5f4f0);
}
QSpinBox, QLineEdit, QComboBox {
    background-color: #ffffff;
    border: 1px solid #7f9db9;
    border-radius: 2px;
    padding: 1px 3px;
    selection-background-color: #316ac5;
}
QLabel { background: transparent; }
QStatusBar {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #4a7bbf, stop:1 #2a5ba0);
    color: #ffffff;
}
QSplitter::handle { background-color: #c0c0b8; }
QSplitter::handle:horizontal { width: 4px; }
QSplitter::handle:vertical   { height: 4px; }
""" + _scrollbar("#ece9d8", "#9ab2cc", "#7f9db9", "#7f9db9")


# ---------------------------------------------------------------------------
# 4. Dark Slate  (charcoal, accent blue)
# ---------------------------------------------------------------------------
_DARK_SLATE = """
QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: "Segoe UI", "Helvetica Neue", sans-serif;
    font-size: 10pt;
}
QMainWindow { background-color: #181825; }
QMenuBar {
    background-color: #181825;
    color: #cdd6f4;
    border-bottom: 1px solid #313244;
}
QMenuBar::item:selected { background-color: #313244; border-radius: 3px; }
QMenu {
    background-color: #1e1e2e;
    border: 1px solid #45475a;
    color: #cdd6f4;
}
QMenu::item { padding: 4px 20px; }
QMenu::item:selected { background-color: #89b4fa; color: #1e1e2e; }
QMenu::separator { background: #45475a; height: 1px; margin: 4px 10px; }
QPushButton {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 4px 10px;
}
QPushButton:hover  { background-color: #45475a; border-color: #89b4fa; }
QPushButton:pressed { background-color: #89b4fa; color: #1e1e2e; }
QSpinBox, QLineEdit, QComboBox {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 2px 6px;
    selection-background-color: #89b4fa;
    selection-color: #1e1e2e;
}
QSpinBox::up-button, QSpinBox::down-button { background: #45475a; border: none; }
QLabel { background: transparent; color: #cdd6f4; }
QStatusBar { background-color: #181825; color: #a6adc8; border-top: 1px solid #313244; }
QSplitter::handle { background-color: #313244; }
QSplitter::handle:horizontal { width: 5px; }
QSplitter::handle:vertical   { height: 5px; }
QSplitter::handle:hover { background-color: #89b4fa; }
QToolTip {
    background-color: #313244; color: #cdd6f4;
    border: 1px solid #89b4fa; border-radius: 3px; padding: 3px;
}
""" + _scrollbar("#181825", "#45475a", "#89b4fa", "#313244")


# ---------------------------------------------------------------------------
# 5. Light Modern  (clean white, flat design, accent teal)
# ---------------------------------------------------------------------------
_LIGHT_MODERN = """
QWidget {
    background-color: #f5f5f5;
    color: #212121;
    font-family: "Segoe UI", "Helvetica Neue", sans-serif;
    font-size: 10pt;
}
QMainWindow { background-color: #fafafa; }
QMenuBar {
    background-color: #ffffff;
    border-bottom: 1px solid #e0e0e0;
}
QMenuBar::item { padding: 4px 10px; }
QMenuBar::item:selected { background-color: #e3f2fd; color: #0288d1; border-radius: 3px; }
QMenu {
    background-color: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
}
QMenu::item { padding: 5px 20px; }
QMenu::item:selected { background-color: #e3f2fd; color: #0288d1; }
QMenu::separator { background: #e0e0e0; height: 1px; margin: 4px 10px; }
QPushButton {
    background-color: #0288d1;
    color: #ffffff;
    border: none;
    border-radius: 4px;
    padding: 5px 14px;
    font-weight: 500;
}
QPushButton:hover  { background-color: #0277bd; }
QPushButton:pressed { background-color: #01579b; }
QSpinBox, QLineEdit, QComboBox {
    background-color: #ffffff;
    color: #212121;
    border: 1px solid #bdbdbd;
    border-radius: 4px;
    padding: 3px 6px;
    selection-background-color: #0288d1;
    selection-color: #ffffff;
}
QSpinBox:focus, QLineEdit:focus, QComboBox:focus { border-color: #0288d1; }
QSpinBox::up-button, QSpinBox::down-button {
    background: #e0e0e0; border: none; width: 14px;
}
QLabel { background: transparent; }
QStatusBar { background-color: #ffffff; border-top: 1px solid #e0e0e0; color: #757575; }
QSplitter::handle { background-color: #e0e0e0; }
QSplitter::handle:horizontal { width: 4px; }
QSplitter::handle:vertical   { height: 4px; }
QSplitter::handle:hover { background-color: #0288d1; }
QToolTip {
    background-color: #ffffff; color: #212121;
    border: 1px solid #0288d1; border-radius: 3px; padding: 3px;
}
""" + _scrollbar("#f5f5f5", "#bdbdbd", "#0288d1", "#e0e0e0")


# ---------------------------------------------------------------------------
# 6. Midnight Blue  (deep navy, gold accents)
# ---------------------------------------------------------------------------
_MIDNIGHT_BLUE = """
QWidget {
    background-color: #0d1b2a;
    color: #e0e0e0;
    font-family: "Segoe UI", "Helvetica Neue", sans-serif;
    font-size: 10pt;
}
QMainWindow { background-color: #0a1520; }
QMenuBar {
    background-color: #0a1520;
    color: #e0e0e0;
    border-bottom: 1px solid #1c3a5a;
}
QMenuBar::item:selected { background-color: #1c3a5a; border-radius: 3px; }
QMenu {
    background-color: #0d1b2a;
    border: 1px solid #1c3a5a;
    color: #e0e0e0;
}
QMenu::item { padding: 4px 20px; }
QMenu::item:selected { background-color: #c9a84c; color: #0d1b2a; }
QMenu::separator { background: #1c3a5a; height: 1px; margin: 4px 10px; }
QPushButton {
    background-color: #1c3a5a;
    color: #e0e0e0;
    border: 1px solid #2a5a8a;
    border-radius: 4px;
    padding: 4px 10px;
}
QPushButton:hover  { background-color: #2a5a8a; border-color: #c9a84c; color: #c9a84c; }
QPushButton:pressed { background-color: #c9a84c; color: #0d1b2a; border-color: #c9a84c; }
QSpinBox, QLineEdit, QComboBox {
    background-color: #1c3a5a;
    color: #e0e0e0;
    border: 1px solid #2a5a8a;
    border-radius: 4px;
    padding: 2px 6px;
    selection-background-color: #c9a84c;
    selection-color: #0d1b2a;
}
QSpinBox::up-button, QSpinBox::down-button { background: #2a5a8a; border: none; }
QLabel { background: transparent; }
QStatusBar { background-color: #0a1520; color: #8a9bb0; border-top: 1px solid #1c3a5a; }
QSplitter::handle { background-color: #1c3a5a; }
QSplitter::handle:horizontal { width: 5px; }
QSplitter::handle:vertical   { height: 5px; }
QSplitter::handle:hover { background-color: #c9a84c; }
QToolTip {
    background-color: #1c3a5a; color: #e0e0e0;
    border: 1px solid #c9a84c; border-radius: 3px; padding: 3px;
}
""" + _scrollbar("#0a1520", "#2a5a8a", "#c9a84c", "#1c3a5a")


# ---------------------------------------------------------------------------
# 7. Solarized Dark
# ---------------------------------------------------------------------------
_SOLARIZED_DARK = """
QWidget {
    background-color: #002b36;
    color: #839496;
    font-family: "Segoe UI", "DejaVu Sans", sans-serif;
    font-size: 10pt;
}
QMainWindow { background-color: #073642; }
QMenuBar {
    background-color: #073642;
    color: #93a1a1;
    border-bottom: 1px solid #586e75;
}
QMenuBar::item:selected { background-color: #586e75; border-radius: 3px; }
QMenu {
    background-color: #002b36;
    border: 1px solid #586e75;
    color: #839496;
}
QMenu::item { padding: 4px 20px; }
QMenu::item:selected { background-color: #268bd2; color: #fdf6e3; }
QMenu::separator { background: #586e75; height: 1px; margin: 4px 10px; }
QPushButton {
    background-color: #073642;
    color: #93a1a1;
    border: 1px solid #586e75;
    border-radius: 4px;
    padding: 4px 10px;
}
QPushButton:hover  { background-color: #586e75; color: #fdf6e3; border-color: #268bd2; }
QPushButton:pressed { background-color: #268bd2; color: #fdf6e3; }
QSpinBox, QLineEdit, QComboBox {
    background-color: #073642;
    color: #839496;
    border: 1px solid #586e75;
    border-radius: 4px;
    padding: 2px 6px;
    selection-background-color: #268bd2;
    selection-color: #fdf6e3;
}
QSpinBox::up-button, QSpinBox::down-button { background: #586e75; border: none; }
QLabel { background: transparent; }
QStatusBar { background-color: #073642; color: #657b83; border-top: 1px solid #586e75; }
QSplitter::handle { background-color: #073642; border: 1px solid #586e75; }
QSplitter::handle:horizontal { width: 5px; }
QSplitter::handle:vertical   { height: 5px; }
QSplitter::handle:hover { background-color: #268bd2; }
QToolTip {
    background-color: #073642; color: #93a1a1;
    border: 1px solid #268bd2; border-radius: 3px; padding: 3px;
}
""" + _scrollbar("#073642", "#586e75", "#268bd2", "#586e75")


# ---------------------------------------------------------------------------
# 8. High Contrast  (accessibility)
# ---------------------------------------------------------------------------
_HIGH_CONTRAST = """
QWidget {
    background-color: #000000;
    color: #ffffff;
    font-family: "Segoe UI", "Tahoma", sans-serif;
    font-size: 11pt;
}
QMainWindow { background-color: #000000; }
QMenuBar {
    background-color: #000000;
    color: #ffffff;
    border-bottom: 2px solid #ffff00;
}
QMenuBar::item:selected { background-color: #ffff00; color: #000000; }
QMenu {
    background-color: #000000;
    border: 2px solid #ffffff;
    color: #ffffff;
}
QMenu::item { padding: 5px 20px; }
QMenu::item:selected { background-color: #ffff00; color: #000000; }
QMenu::separator { background: #ffffff; height: 2px; margin: 4px 10px; }
QPushButton {
    background-color: #000000;
    color: #ffffff;
    border: 2px solid #ffffff;
    padding: 4px 10px;
    font-weight: bold;
}
QPushButton:hover  { background-color: #ffff00; color: #000000; border-color: #ffff00; }
QPushButton:pressed { background-color: #ffffff; color: #000000; }
QSpinBox, QLineEdit, QComboBox {
    background-color: #000000;
    color: #ffffff;
    border: 2px solid #ffffff;
    padding: 2px 6px;
    selection-background-color: #ffff00;
    selection-color: #000000;
}
QLabel { background: transparent; }
QStatusBar { background-color: #000000; color: #ffff00; border-top: 2px solid #ffff00; }
QSplitter::handle { background-color: #ffffff; }
QSplitter::handle:horizontal { width: 6px; }
QSplitter::handle:vertical   { height: 6px; }
QSplitter::handle:hover { background-color: #ffff00; }
QToolTip {
    background-color: #000000; color: #ffff00;
    border: 2px solid #ffff00; padding: 3px;
}
""" + _scrollbar("#000000", "#ffffff", "#ffff00", "#ffffff")


# ---------------------------------------------------------------------------
# 9. Warm Earth  (beige tones, terracotta accents)
# ---------------------------------------------------------------------------
_WARM_EARTH = """
QWidget {
    background-color: #f2ede4;
    color: #3d2b1f;
    font-family: "Georgia", "Palatino", serif;
    font-size: 10pt;
}
QMainWindow { background-color: #ebe4d8; }
QMenuBar {
    background-color: #c8b89a;
    color: #3d2b1f;
    border-bottom: 1px solid #a0876a;
}
QMenuBar::item:selected { background-color: #a0876a; color: #f2ede4; border-radius: 2px; }
QMenu {
    background-color: #f2ede4;
    border: 1px solid #a0876a;
    color: #3d2b1f;
}
QMenu::item { padding: 4px 20px; }
QMenu::item:selected { background-color: #b85c38; color: #f2ede4; }
QMenu::separator { background: #c8b89a; height: 1px; margin: 4px 10px; }
QPushButton {
    background-color: #c8b89a;
    color: #3d2b1f;
    border: 1px solid #a0876a;
    border-radius: 4px;
    padding: 4px 10px;
}
QPushButton:hover  { background-color: #b85c38; color: #f2ede4; border-color: #8b3a22; }
QPushButton:pressed { background-color: #8b3a22; color: #f2ede4; }
QSpinBox, QLineEdit, QComboBox {
    background-color: #faf7f2;
    color: #3d2b1f;
    border: 1px solid #a0876a;
    border-radius: 3px;
    padding: 2px 6px;
    selection-background-color: #b85c38;
    selection-color: #f2ede4;
}
QSpinBox::up-button, QSpinBox::down-button { background: #c8b89a; border: none; }
QLabel { background: transparent; }
QStatusBar { background-color: #c8b89a; color: #3d2b1f; border-top: 1px solid #a0876a; }
QSplitter::handle { background-color: #c8b89a; }
QSplitter::handle:horizontal { width: 4px; }
QSplitter::handle:vertical   { height: 4px; }
QSplitter::handle:hover { background-color: #b85c38; }
QToolTip {
    background-color: #f2ede4; color: #3d2b1f;
    border: 1px solid #b85c38; border-radius: 3px; padding: 3px;
}
""" + _scrollbar("#ebe4d8", "#c8b89a", "#b85c38", "#a0876a")


# ---------------------------------------------------------------------------
# Public registry
# ---------------------------------------------------------------------------

STYLESHEETS: List[Tuple[str, str]] = [
    ("System Default",   _SYSTEM_DEFAULT),
    ("Windows Classic",  _WINDOWS_CLASSIC),
    ("Windows XP",       _WINDOWS_XP),
    ("Dark Slate",       _DARK_SLATE),
    ("Light Modern",     _LIGHT_MODERN),
    ("Midnight Blue",    _MIDNIGHT_BLUE),
    ("Solarized Dark",   _SOLARIZED_DARK),
    ("High Contrast",    _HIGH_CONTRAST),
    ("Warm Earth",       _WARM_EARTH),
]
