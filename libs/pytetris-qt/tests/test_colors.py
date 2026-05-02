"""Tests for pytetris_qt.colors."""

from PyQt6.QtGui import QColor
from pytetris_qt.colors import BACKGROUND_COLOR, BLOCK_COLORS, BORDER_COLOR, WALL_COLOR


class TestBlockColors:
    def test_all_seven_blocks_have_colors(self) -> None:
        for number in range(1, 8):
            assert number in BLOCK_COLORS

    def test_colors_are_qcolor_instances(self) -> None:
        for color in BLOCK_COLORS.values():
            assert isinstance(color, QColor)

    def test_i_block_is_sky_blue(self) -> None:
        c = BLOCK_COLORS[1]
        assert c.red() == 80
        assert c.green() == 188
        assert c.blue() == 223

    def test_constants_are_qcolor(self) -> None:
        assert isinstance(BACKGROUND_COLOR, QColor)
        assert isinstance(BORDER_COLOR, QColor)
        assert isinstance(WALL_COLOR, QColor)
