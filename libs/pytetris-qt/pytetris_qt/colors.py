"""Block colour mapping for PyTetris Qt widgets.

Maps each block number (1–7) to its canonical :class:`~PyQt6.QtGui.QColor`,
plus colour constants for walls, the empty cell background, and cell borders.
"""

from PyQt6.QtGui import QColor

#: Maps block number → fill colour.  Index 0 is unused (empty cells).
BLOCK_COLORS: dict[int, QColor] = {
    1: QColor(80, 188, 223),   # I — sky-blue
    2: QColor(0, 0, 255),      # J — blue
    3: QColor(255, 127, 0),    # L — orange
    4: QColor(255, 212, 0),    # O — yellow
    5: QColor(129, 193, 71),   # S — green
    6: QColor(153, 0, 255),    # T — purple
    7: QColor(255, 0, 0),      # Z — red
}

#: Colour used for wall / floor cells (block number 8).
WALL_COLOR: QColor = QColor(128, 128, 128)

#: Colour used for the thin grid-line border drawn around each cell.
BORDER_COLOR: QColor = QColor(0, 0, 0)

#: Background colour for empty cells and the overall board.
BACKGROUND_COLOR: QColor = QColor(0, 0, 0)

#: Colour for the faint grid guide drawn inside the play area.
GRID_GUIDE_COLOR: QColor = QColor(161, 145, 61)
