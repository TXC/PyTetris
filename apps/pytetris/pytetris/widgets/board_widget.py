"""Board widget — renders the Tetris play field using QPainter."""

import logging

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QKeyEvent, QPainter, QPaintEvent
from PyQt6.QtWidgets import QWidget
from pytetris_core.game import COLS, ROWS
from pytetris_core.models import BackgroundBlock, Move
from pytetris_qt.colors import (
    BACKGROUND_COLOR,
    BLOCK_COLORS,
    BORDER_COLOR,
    GRID_GUIDE_COLOR,
    WALL_COLOR,
)

log = logging.getLogger(__name__)

#: Width and height of each grid cell in pixels.
CELL_SIZE: int = 32

#: Width of the thin guide line drawn inside each play-area cell.
GUIDE_LINE_WIDTH: int = 1

#: Play area spans columns 1–10; column 0 and 11 are walls.
PLAY_COLS_START: int = 1
PLAY_COLS_END: int = COLS - 1  # exclusive

#: Floor is at row 20; rows 0–19 are the play area.
PLAY_ROWS_END: int = ROWS - 1  # exclusive


class BoardWidget(QWidget):
    """Renders the 10×20 Tetris play field.

    This widget only draws the current state of the
    :class:`~pytetris_core.game.TetrisGame` grid that is exposed through the
    ``grid`` property.  All game logic is delegated to the controller via the
    emitted signals.

    Signals:
        move_requested: Emitted when the user presses an arrow key.
    """

    move_requested: pyqtSignal = pyqtSignal(Move)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._grid: list[list[BackgroundBlock]] = []
        self.setFixedSize(
            COLS * CELL_SIZE,
            ROWS * CELL_SIZE,
        )
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_grid(self, grid: list[list[BackgroundBlock]]) -> None:
        """Update the grid reference and trigger a repaint.

        :param grid: The game grid from :attr:`~TetrisGame.grid`.
        """
        self._grid = grid
        self.update()

    # ------------------------------------------------------------------
    # Qt event overrides
    # ------------------------------------------------------------------

    def paintEvent(self, event: QPaintEvent | None) -> None:  # noqa: N802
        """Draw the board."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), BACKGROUND_COLOR)
        if not self._grid:
            return
        self._draw_play_area_guides(painter)
        self._draw_cells(painter)

    def keyPressEvent(self, event: QKeyEvent | None) -> None:  # noqa: N802
        """Translate arrow-key presses into :attr:`move_requested` signals."""
        if event is None:
            return
        key = event.key()
        match key:
            case Qt.Key.Key_Up:
                self.move_requested.emit(Move.UP)
            case Qt.Key.Key_Left:
                self.move_requested.emit(Move.LEFT)
            case Qt.Key.Key_Right:
                self.move_requested.emit(Move.RIGHT)
            case Qt.Key.Key_Down:
                self.move_requested.emit(Move.DOWN)
            case _:
                super().keyPressEvent(event)

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------

    def _draw_play_area_guides(self, painter: QPainter) -> None:
        """Draw faint grid lines over the play area."""
        painter.setPen(GRID_GUIDE_COLOR)
        for col in range(PLAY_COLS_START, PLAY_COLS_END):
            for row in range(PLAY_ROWS_END):
                x = col * CELL_SIZE
                y = row * CELL_SIZE
                painter.drawRect(x, y, CELL_SIZE, CELL_SIZE)

    def _draw_cells(self, painter: QPainter) -> None:
        """Fill each non-empty cell with its colour."""
        for row in range(ROWS):
            for col in range(COLS):
                cell = self._grid[row][col]
                color = self._cell_color(cell)
                if color is None:
                    continue
                x = col * CELL_SIZE
                y = row * CELL_SIZE
                painter.fillRect(x, y, CELL_SIZE, CELL_SIZE, color)
                painter.setPen(BORDER_COLOR)
                painter.drawRect(x, y, CELL_SIZE - 1, CELL_SIZE - 1)

    @staticmethod
    def _cell_color(cell: BackgroundBlock) -> QColor | None:
        """Return the fill colour for *cell*, or ``None`` if it should not be drawn."""
        if cell.number in BLOCK_COLORS:
            return BLOCK_COLORS[cell.number]
        if cell.number == 8:
            return WALL_COLOR
        return None
