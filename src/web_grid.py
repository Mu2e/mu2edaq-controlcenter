"""
web_grid.py - Resizable, rearrangeable grid of embedded web pages.

Each cell in the grid contains a WebCell which embeds a QWebEngineView.
The user can:
  - Drag cells to swap their positions
  - Right-click a cell for options (reload, set URL, move)
  - Resize the grid via the main window controls (adds/removes rows/cols)
  - Drag splitter handles to resize cells interactively
"""

from typing import Dict, List, Optional, Tuple

from PyQt6.QtCore import QMimeData, QUrl, Qt, pyqtSignal
from PyQt6.QtGui import QDrag, QPixmap
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import (
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

_ZOOM_MIN = 0.25
_ZOOM_MAX = 5.0
_ZOOM_STEP = 0.25
_ZOOM_DEFAULT = 1.0


class WebCell(QFrame):
    """A single cell in the grid: a title bar with zoom controls + embedded web view."""

    swap_requested = pyqtSignal(object, object)  # (source WebCell, target WebCell)

    def __init__(self, name: str, url: str, zoom: float = _ZOOM_DEFAULT, parent=None):
        super().__init__(parent)
        self._name = name
        self._url = url

        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setLineWidth(1)
        self.setAcceptDrops(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- Title bar -------------------------------------------------------
        title_widget = QWidget()
        title_widget.setFixedHeight(26)
        title_widget.setStyleSheet("background: #2c3e50;")
        hbox = QHBoxLayout(title_widget)
        hbox.setContentsMargins(4, 0, 2, 0)
        hbox.setSpacing(2)

        self._title_label = QLabel(name)
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self._title_label.setStyleSheet(
            "QLabel { color: #ecf0f1; font-weight: bold; font-size: 10pt; background: transparent; }"
        )
        self._title_label.setToolTip(url)
        hbox.addWidget(self._title_label, stretch=1)

        btn_style = (
            "QPushButton { color: #ecf0f1; background: #3d566e; border: none; "
            "border-radius: 2px; font-size: 11pt; font-weight: bold; padding: 0px 3px; }"
            "QPushButton:hover { background: #5d7a8e; }"
            "QPushButton:pressed { background: #2c3e50; }"
        )

        zoom_out_btn = QPushButton("−")
        zoom_out_btn.setFixedSize(22, 20)
        zoom_out_btn.setStyleSheet(btn_style)
        zoom_out_btn.setToolTip("Zoom out")
        zoom_out_btn.clicked.connect(self._zoom_out)
        hbox.addWidget(zoom_out_btn)

        self._zoom_label = QLabel("100%")
        self._zoom_label.setFixedWidth(42)
        self._zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._zoom_label.setStyleSheet(
            "QLabel { color: #ecf0f1; font-size: 8pt; background: transparent; cursor: pointer; }"
        )
        self._zoom_label.setToolTip("Click to set zoom level")
        self._zoom_label.mousePressEvent = lambda _e: self._zoom_set_dialog()
        hbox.addWidget(self._zoom_label)

        zoom_in_btn = QPushButton("+")
        zoom_in_btn.setFixedSize(22, 20)
        zoom_in_btn.setStyleSheet(btn_style)
        zoom_in_btn.setToolTip("Zoom in")
        zoom_in_btn.clicked.connect(self._zoom_in)
        hbox.addWidget(zoom_in_btn)

        layout.addWidget(title_widget)

        # --- Web view --------------------------------------------------------
        self._web_view = QWebEngineView()
        self._web_view.setUrl(QUrl(url))
        layout.addWidget(self._web_view)

        # Apply initial zoom (after web view exists)
        self.set_zoom(zoom)

    # --- Properties ----------------------------------------------------------

    @property
    def name(self) -> str:
        return self._name

    @property
    def url(self) -> str:
        return self._url

    @property
    def zoom(self) -> float:
        return self._web_view.zoomFactor()

    # --- Page / zoom mutations -----------------------------------------------

    def set_page(self, name: str, url: str) -> None:
        self._name = name
        self._url = url
        self._title_label.setText(name)
        self._title_label.setToolTip(url)
        self._web_view.setUrl(QUrl(url))

    def set_zoom(self, factor: float) -> None:
        factor = max(_ZOOM_MIN, min(_ZOOM_MAX, factor))
        self._web_view.setZoomFactor(factor)
        self._zoom_label.setText(f"{round(factor * 100)}%")

    def reload(self) -> None:
        self._web_view.reload()

    # --- Zoom helpers --------------------------------------------------------

    def _zoom_in(self) -> None:
        self.set_zoom(round(self.zoom + _ZOOM_STEP, 2))

    def _zoom_out(self) -> None:
        self.set_zoom(round(self.zoom - _ZOOM_STEP, 2))

    def _zoom_set_dialog(self) -> None:
        current_pct = round(self.zoom * 100)
        pct, ok = QInputDialog.getInt(
            self, "Set Zoom", "Zoom percentage (25–500):",
            value=current_pct, min=25, max=500, step=25,
        )
        if ok:
            self.set_zoom(pct / 100.0)

    # --- Drag and drop -------------------------------------------------------

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        drag = QDrag(self)
        mime = QMimeData()
        mime.setText("webcell")
        drag.setMimeData(mime)
        pix = QPixmap(self.size())
        self.render(pix)
        drag.setPixmap(pix.scaled(120, 80, Qt.AspectRatioMode.KeepAspectRatio))
        drag.exec(Qt.DropAction.MoveAction)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText() and event.mimeData().text() == "webcell":
            event.acceptProposedAction()
            self.setStyleSheet(self.styleSheet() + "QFrame { border: 2px dashed #3498db; }")

    def dragLeaveEvent(self, event):
        self.setStyleSheet("")

    def dropEvent(self, event):
        self.setStyleSheet("")
        source = event.source()
        if isinstance(source, WebCell) and source is not self:
            self.swap_requested.emit(source, self)
        event.acceptProposedAction()

    # --- Context menu --------------------------------------------------------

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        reload_act = menu.addAction("Reload")
        set_url_act = menu.addAction("Set URL...")
        set_name_act = menu.addAction("Rename...")
        menu.addSeparator()
        zoom_in_act = menu.addAction("Zoom In (+25%)")
        zoom_out_act = menu.addAction("Zoom Out (−25%)")
        zoom_set_act = menu.addAction("Set Zoom...")
        zoom_reset_act = menu.addAction("Reset Zoom")
        menu.addSeparator()
        clear_act = menu.addAction("Clear (blank)")

        action = menu.exec(event.globalPos())
        if action == reload_act:
            self.reload()
        elif action == set_url_act:
            url, ok = QInputDialog.getText(
                self, "Set URL", "Enter URL:", QLineEdit.EchoMode.Normal, self._url
            )
            if ok and url.strip():
                self.set_page(self._name, url.strip())
        elif action == set_name_act:
            name, ok = QInputDialog.getText(
                self, "Rename", "Enter name:", QLineEdit.EchoMode.Normal, self._name
            )
            if ok and name.strip():
                self.set_page(name.strip(), self._url)
        elif action == zoom_in_act:
            self._zoom_in()
        elif action == zoom_out_act:
            self._zoom_out()
        elif action == zoom_set_act:
            self._zoom_set_dialog()
        elif action == zoom_reset_act:
            self.set_zoom(_ZOOM_DEFAULT)
        elif action == clear_act:
            self.set_page(self._name, "about:blank")


class WebGrid(QWidget):
    """
    Grid container using nested QSplitters so cells can be resized by dragging.

    Layout:
        QVBoxLayout
          └─ QSplitter (vertical)   ← rows
               ├─ QSplitter (horizontal)  ← cols in row 0
               │    ├─ WebCell [0,0]
               │    └─ WebCell [0,1]
               └─ QSplitter (horizontal)  ← cols in row 1
                    ├─ WebCell [1,0]
                    └─ WebCell [1,1]
    """

    def __init__(self, rows: int, cols: int, pages: List[Dict], parent=None):
        super().__init__(parent)
        self._rows = rows
        self._cols = cols

        outer = QVBoxLayout(self)
        outer.setContentsMargins(4, 4, 4, 4)
        outer.setSpacing(0)

        self._vsplitter = QSplitter(Qt.Orientation.Vertical)
        self._vsplitter.setChildrenCollapsible(False)
        outer.addWidget(self._vsplitter)

        # cells[row][col] -> WebCell
        self._cells: List[List[Optional[WebCell]]] = []
        # row_splitters[row] -> QSplitter
        self._row_splitters: List[QSplitter] = []

        self._init_grid(pages)

    # --- Initialisation ------------------------------------------------------

    def _init_grid(self, pages: List[Dict]) -> None:
        self._cells = [
            [None for _ in range(self._cols)] for _ in range(self._rows)
        ]
        self._row_splitters = []

        # Assign explicit positions first
        placed: Dict[Tuple[int, int], Dict] = {}
        unplaced: List[Dict] = []
        for page in pages:
            pos = page.get("position")
            if (
                pos
                and 0 <= pos[0] < self._rows
                and 0 <= pos[1] < self._cols
                and (pos[0], pos[1]) not in placed
            ):
                placed[(pos[0], pos[1])] = page
            else:
                unplaced.append(page)

        unplaced_iter = iter(unplaced)
        for r in range(self._rows):
            hsplitter = QSplitter(Qt.Orientation.Horizontal)
            hsplitter.setChildrenCollapsible(False)
            self._vsplitter.addWidget(hsplitter)
            self._row_splitters.append(hsplitter)

            for c in range(self._cols):
                if (r, c) in placed:
                    page = placed[(r, c)]
                else:
                    try:
                        page = next(unplaced_iter)
                    except StopIteration:
                        page = {"name": f"[{r},{c}]", "url": "about:blank"}

                cell = self._make_cell(page["name"], page["url"], float(page.get("zoom", _ZOOM_DEFAULT)))
                self._cells[r][c] = cell
                hsplitter.addWidget(cell)

        # Equal initial sizes for rows and columns
        row_h = 10000 // self._rows
        self._vsplitter.setSizes([row_h] * self._rows)
        for hsplitter in self._row_splitters:
            col_w = 10000 // self._cols
            hsplitter.setSizes([col_w] * self._cols)

    def _make_cell(self, name: str, url: str, zoom: float = _ZOOM_DEFAULT) -> WebCell:
        cell = WebCell(name, url, zoom, self)
        cell.swap_requested.connect(self._swap_cells)
        return cell

    # --- Grid resize ---------------------------------------------------------

    def set_grid_size(self, rows: int, cols: int) -> None:
        """Resize the grid, preserving existing page assignments."""
        existing = []
        for r in range(self._rows):
            for c in range(self._cols):
                cell = self._cells[r][c]
                if cell:
                    existing.append({"name": cell.name, "url": cell.url, "zoom": cell.zoom})

        # Remove all row splitters from the vertical splitter
        for hsplitter in self._row_splitters:
            hsplitter.setParent(None)
            hsplitter.deleteLater()

        self._rows = rows
        self._cols = cols
        self._init_grid(existing)

    @property
    def rows(self) -> int:
        return self._rows

    @property
    def cols(self) -> int:
        return self._cols

    def set_cell(self, row: int, col: int, name: str, url: str, zoom: float = _ZOOM_DEFAULT) -> None:
        """Update a single cell's page without rebuilding the grid."""
        if 0 <= row < self._rows and 0 <= col < self._cols:
            cell = self._cells[row][col]
            if cell:
                cell.set_page(name, url)
                cell.set_zoom(zoom)

    # --- Swap ----------------------------------------------------------------

    def _swap_cells(self, src: WebCell, dst: WebCell) -> None:
        """Swap the page content (name, url, zoom) between two cells."""
        src_name, src_url, src_zoom = src.name, src.url, src.zoom
        src.set_page(dst.name, dst.url)
        src.set_zoom(dst.zoom)
        dst.set_page(src_name, src_url)
        dst.set_zoom(src_zoom)

    # --- Reload all ----------------------------------------------------------

    def reload_all(self) -> None:
        for row in self._cells:
            for cell in row:
                if cell:
                    cell.reload()

    # --- Snapshot of current layout ------------------------------------------

    def get_pages(self) -> List[Dict]:
        """Return the current page assignments as a list of page dicts."""
        pages = []
        for r, row in enumerate(self._cells):
            for c, cell in enumerate(row):
                if cell:
                    pages.append({
                        "name": cell.name,
                        "url": cell.url,
                        "zoom": cell.zoom,
                        "position": [r, c],
                    })
        return pages

    def get_splitter_sizes(self) -> Dict:
        """Return current splitter sizes for save/restore."""
        return {
            "vertical": self._vsplitter.sizes(),
            "horizontal": [s.sizes() for s in self._row_splitters],
        }

    def apply_splitter_sizes(self, sizes: Dict) -> None:
        """Restore splitter sizes previously returned by get_splitter_sizes()."""
        v = sizes.get("vertical", [])
        if v and len(v) == self._vsplitter.count():
            self._vsplitter.setSizes(v)
        h_list = sizes.get("horizontal", [])
        for i, hsplitter in enumerate(self._row_splitters):
            if i < len(h_list) and len(h_list[i]) == hsplitter.count():
                hsplitter.setSizes(h_list[i])
