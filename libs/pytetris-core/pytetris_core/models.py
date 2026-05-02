"""Data models for the PyTetris game engine."""

import dataclasses
from enum import Enum


@dataclasses.dataclass
class BackgroundBlock:
    """A single cell in the Tetris game grid.

    Cells use zero-based grid coordinates: ``col`` 0 and 11 are the left/right
    walls; ``row`` 20 is the floor.  ``number`` encodes the cell content and
    ``is_occupied`` indicates whether the cell blocks movement.

    :param col: Grid column (0-11).
    :param row: Grid row (0-20).
    :param number: 0 = empty, 1-7 = placed block colour, 8 = wall/floor.
    :param is_occupied: ``True`` if the cell is a wall, floor, or placed block.
    """

    col: int
    row: int
    number: int
    is_occupied: bool


class Move(Enum):
    """Directional movement options available to the player."""

    UP = 0
    LEFT = 1
    RIGHT = 2
    DOWN = 3
