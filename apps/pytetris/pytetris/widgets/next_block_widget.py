"""Next-block preview widget."""

import logging

from PyQt6.QtGui import QPainter, QPaintEvent
from PyQt6.QtWidgets import QWidget
from pytetris_core.blocks import Block
from pytetris_qt.colors import (
    BACKGROUND_COLOR,
    BLOCK_COLORS,
    BORDER_COLOR,
)

log = logging.getLogger(__name__)

#: Cell size for the preview (same as the board).
PREVIEW_CELL: int = 32

#: Number of rows/columns in the preview bounding box.
PREVIEW_GRID: int = 4


class NextBlockWidget(QWidget):
    """Renders the upcoming block in a 4x4 preview grid.

    :param parent: Optional parent widget.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._block: Block | None = None
        total = PREVIEW_GRID * PREVIEW_CELL
        self.setFixedSize(total, total)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_block(self, block: Block | None) -> None:
        """Update the displayed next block and repaint.

        :param block: The next block to preview, or ``None`` to clear.
        """
        self._block = block
        self.update()

    # ------------------------------------------------------------------
    # Qt event overrides
    # ------------------------------------------------------------------

    def paintEvent(self, event: QPaintEvent | None) -> None:  # noqa: N802
        """Draw the preview grid."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), BACKGROUND_COLOR)
        if self._block is None:
            return
        color = BLOCK_COLORS.get(self._block.number)
        if color is None:
            return
        for row_offset, col_offset in self._block.SHAPE:
            x = col_offset * PREVIEW_CELL
            y = row_offset * PREVIEW_CELL
            painter.fillRect(x, y, PREVIEW_CELL, PREVIEW_CELL, color)
            painter.setPen(BORDER_COLOR)
            painter.drawRect(x, y, PREVIEW_CELL - 1, PREVIEW_CELL - 1)
