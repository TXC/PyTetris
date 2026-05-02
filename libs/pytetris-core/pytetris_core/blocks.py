"""Tetris block (tetromino) definitions for the PyTetris game engine.

Each concrete block class encapsulates its own rotation logic and preview
shape.  All blocks operate on the :class:`~pytetris_core.game.TetrisGame`
grid through the ``tetris`` reference they receive at construction.

No display framework is imported here — rendering is the responsibility of
the application layer.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Protocol

if TYPE_CHECKING:
    from .game import TetrisGame


class Block(Protocol):
    """Protocol that every concrete Tetris block must satisfy."""

    #: Integer identifier (1–7) matching the block's colour slot.
    number: int

    #: Preview shape as ``(row_offset, col_offset)`` tuples relative to the
    #: top-left corner of a 4×4 bounding box.
    SHAPE: ClassVar[list[tuple[int, int]]]

    @property
    def turnable(self) -> bool:
        """Return ``True`` if the block can rotate in its current position."""
        ...

    def render_background_blocks(self) -> None:
        """Update :attr:`~TetrisGame.current_blocks` for the next rotation."""
        ...

    def turn(self) -> None:
        """Attempt to rotate the block, updating the grid if possible."""
        ...


# ---------------------------------------------------------------------------
# Concrete block implementations
# ---------------------------------------------------------------------------


class BlockI:
    """I-shaped (straight) Tetromino — block number 1.

    :param tetris: The game instance this block belongs to.
    """

    SHAPE: ClassVar[list[tuple[int, int]]] = [
        (1, 0),
        (1, 1),
        (1, 2),
        (1, 3),
    ]

    def __init__(self, tetris: TetrisGame) -> None:
        self.number = 1
        self.tetris = tetris
        self._turnable_check_indexes = [
            (0, 0),
            (0, 3),
            (0, 0),
            (0, 0),
        ]
        self._render_block_indexes = [
            (2, 2),
            (1, 1),
            (2, 2),
            (1, 1),
        ]
        self._turnable_offset_iters: list[list[tuple[int, int]]] = [
            [(y, x) for x in range(4) for y in [-1, 1, 2]],
            [
                *((y, -1) for y in range(4)),
                *((y, 1) for y in range(4)),
                *((y, -2) for y in range(4)),
            ],
            [(y, -x) for x in range(4) for y in [1, -1, -2]],
            [
                *((y, -1) for y in range(4)),
                *((y, 1) for y in range(4)),
                *((y, 2) for y in range(4)),
            ],
        ]
        self._render_offset_iters: list[list[tuple[int, int]]] = [
            [(2 - y, 0) for y in range(4)],
            [(0, 1 - x) for x in range(4)],
            [(y - 2, 0) for y in range(4)],
            [(0, x - 1) for x in range(4)],
        ]

    @property
    def turnable(self) -> bool:
        """Return ``True`` if the I-block can rotate."""
        state = self.tetris.state
        if state == 0 and self.tetris.current_rows[0] == 0:
            return False
        row_i, col_i = self._turnable_check_indexes[state]
        current_row = self.tetris.current_rows[row_i]
        current_col = self.tetris.current_cols[col_i]
        for oy, ox in self._turnable_offset_iters[state]:
            if self.tetris.grid[current_row + oy][current_col + ox].is_occupied:
                return False
        return True

    def render_background_blocks(self) -> None:
        """Place the I-block cells in the new rotation position."""
        state = self.tetris.state
        row_i, col_i = self._render_block_indexes[state]
        current_row = self.tetris.current_rows[row_i]
        current_col = self.tetris.current_cols[col_i]
        for i, (oy, ox) in enumerate(self._render_offset_iters[state]):
            block = self.tetris.grid[current_row + oy][current_col + ox]
            block.number = self.tetris.block_number
            self.tetris.current_blocks[i] = block

    def turn(self) -> None:
        """Rotate the I-block if possible."""
        self.tetris.refresh()
        self.tetris.rotate(self)


class BlockJ:
    """J-shaped Tetromino — block number 2.

    :param tetris: The game instance this block belongs to.
    """

    SHAPE: ClassVar[list[tuple[int, int]]] = [
        (0, 0),
        (1, 0),
        (1, 1),
        (1, 2),
    ]

    def __init__(self, tetris: TetrisGame) -> None:
        self.number = 2
        self.tetris = tetris
        self._turnable_check_indexes: list[list[tuple[int, int]]] = [
            [(1, 1), (0, 0)],
            [(1, 1), (0, 0)],
            [(1, 1), (0, 0)],
            [(3, 1), (0, 0)],
        ]
        self._render_block_indexes: list[list[tuple[int, int]]] = [
            [(0, 0), (2, 2)],
            [(0, 0), (0, 0)],
            [(0, 0), (2, 2)],
            [(0, 0), (0, 0)],
        ]

        from collections.abc import Callable

        self._turnable_offsets: list[
            list[Callable[[int], tuple[int, int]]]
        ] = [
            [lambda x: (1, x), lambda x: (0, x + 1)],
            [lambda y: (y, -1), lambda y: (y + 1, 0)],
            [lambda x: (-1, -x), lambda x: (0, x - 1)],
            [lambda y: (y, 1), lambda y: (y - 2, 0)],
        ]
        self._render_offsets: list[
            list[tuple[int, int] | Callable[[int], tuple[int, int]]]
        ] = [
            [(0, 2), lambda y: (y - 1, 0)],
            [(2, 0), lambda x: (1, -x)],
            [(0, -2), lambda y: (1 - y, 0)],
            [(-2, 0), lambda x: (-1, x)],
        ]

    @property
    def turnable(self) -> bool:
        """Return ``True`` if the J-block can rotate."""
        state = self.tetris.state
        coords = [
            (self.tetris.current_rows[r], self.tetris.current_cols[c])
            for r, c in self._turnable_check_indexes[state]
        ]
        blocks_to_check = zip(
            coords, self._turnable_offsets[state], [3, 2], strict=False
        )
        for (row, col), offset_func, offsets in blocks_to_check:
            for i in range(offsets):
                oy, ox = offset_func(i)
                if self.tetris.grid[row + oy][col + ox].is_occupied:
                    return False
        return True

    def render_background_blocks(self) -> None:
        """Place the J-block cells in the new rotation position."""
        state = self.tetris.state
        (r1, c1), (r2, c2) = self._render_block_indexes[state]
        current_row = self.tetris.current_rows[r1]
        current_col = self.tetris.current_cols[c1]

        offset, offset_func = self._render_offsets[state]
        assert isinstance(offset, tuple)
        block = self.tetris.grid[current_row + offset[0]][
            current_col + offset[1]
        ]
        block.number = self.tetris.block_number
        self.tetris.current_blocks[0] = block

        current_row = self.tetris.current_rows[r2]
        current_col = self.tetris.current_cols[c2]
        assert callable(offset_func)
        for i in range(3):
            oy, ox = offset_func(i)
            block = self.tetris.grid[current_row + oy][current_col + ox]
            block.number = self.tetris.block_number
            self.tetris.current_blocks[i + 1] = block

    def turn(self) -> None:
        """Rotate the J-block if possible."""
        self.tetris.refresh()
        self.tetris.rotate(self)


class BlockL:
    """L-shaped Tetromino — block number 3.

    :param tetris: The game instance this block belongs to.
    """

    SHAPE: ClassVar[list[tuple[int, int]]] = [
        (0, 2),
        (1, 0),
        (1, 1),
        (1, 2),
    ]

    def __init__(self, tetris: TetrisGame) -> None:
        self.number = 3
        self.tetris = tetris

        self._turnable_check_indexes: list[list[tuple[int, int]]] = [
            [(0, 0), (3, 3)],
            [(0, 0), (0, 0)],
            [(2, 2), (3, 3)],
            [(2, 0), (3, 3)],
        ]
        self._render_block_indexes: list[list[tuple[int, int]]] = [
            [(1, 1), (2, 2)],
            [(1, 1), (2, 2)],
            [(1, 1), (2, 2)],
            [(1, 1), (2, 2)],
        ]

        from collections.abc import Callable

        self._turnable_offsets: list[
            list[Callable[[int], tuple[int, int]]]
        ] = [
            [lambda x: (1, x), lambda x: (3, x - 2)],
            [lambda y: (y, -1), lambda y: (y, 1)],
            [lambda x: (-1, x), lambda x: (0, x + 1)],
            [lambda y: (y, 1), lambda y: (y + 1, 0)],
        ]
        self._render_offsets: list[
            list[Callable[[int], tuple[int, int]] | tuple[int, int]]
        ] = [
            [lambda y: (y - 1, 0), (1, 0)],
            [lambda x: (0, 1 - x), (0, -1)],
            [lambda y: (1 - y, 0), (-1, 0)],
            [lambda x: (0, x - 1), (0, 1)],
        ]

    @property
    def turnable(self) -> bool:
        """Return ``True`` if the L-block can rotate."""
        state = self.tetris.state
        coords = [
            (self.tetris.current_rows[r], self.tetris.current_cols[c])
            for r, c in self._turnable_check_indexes[state]
        ]
        blocks_to_check = zip(
            coords, self._turnable_offsets[state], [3, 2], strict=False
        )
        for (row, col), offset_func, offsets in blocks_to_check:
            for i in range(offsets):
                oy, ox = offset_func(i)
                if self.tetris.grid[row + oy][col + ox].is_occupied:
                    return False
        return True

    def render_background_blocks(self) -> None:
        """Place the L-block cells in the new rotation position."""
        state = self.tetris.state
        offset_func, offset = self._render_offsets[state]
        (r1, c1), (r2, c2) = self._render_block_indexes[state]
        current_row = self.tetris.current_rows[r1]
        current_col = self.tetris.current_cols[c1]
        assert callable(offset_func)
        for i in range(3):
            oy, ox = offset_func(i)
            block = self.tetris.grid[current_row + oy][current_col + ox]
            block.number = self.tetris.block_number
            self.tetris.current_blocks[i] = block
        current_row = self.tetris.current_rows[r2]
        current_col = self.tetris.current_cols[c2]
        assert isinstance(offset, tuple)
        block = self.tetris.grid[current_row + offset[0]][
            current_col + offset[1]
        ]
        block.number = self.tetris.block_number
        self.tetris.current_blocks[3] = block

    def turn(self) -> None:
        """Rotate the L-block if possible."""
        self.tetris.refresh()
        self.tetris.rotate(self)


class BlockO:
    """O-shaped (square) Tetromino — block number 4.

    The O-block does not rotate.

    :param tetris: The game instance this block belongs to.
    """

    SHAPE: ClassVar[list[tuple[int, int]]] = [
        (0, 0),
        (0, 1),
        (1, 0),
        (1, 1),
    ]

    def __init__(self, tetris: TetrisGame) -> None:
        self.number = 4
        self.tetris = tetris

    @property
    def turnable(self) -> bool:
        """Return ``False`` — the O-block never rotates."""
        return False

    def render_background_blocks(self) -> None:
        """No-op: the O-block does not have rotation states."""

    def turn(self) -> None:
        """No-op: the O-block does not rotate."""


class BlockS:
    """S-shaped Tetromino — block number 5.

    :param tetris: The game instance this block belongs to.
    """

    SHAPE: ClassVar[list[tuple[int, int]]] = [
        (0, 1),
        (0, 2),
        (1, 0),
        (1, 1),
    ]

    def __init__(self, tetris: TetrisGame) -> None:
        self.number = 5
        self.tetris = tetris

        self._turnable_check_indexes: list[list[tuple[int, int]]] = [
            [(2, 0), (0, 0), (1, 1)],
            [(0, 2), (1, 1), (2, 2)],
            [(2, 3), (0, 0), (2, 0)],
            [(0, 2), (1, 1), (2, 2)],
        ]
        self._render_block_indexes: list[list[tuple[int, int]]] = [
            [(0, 0), (1, 1)],
            [(0, 0), (1, 1)],
            [(0, 0), (1, 1)],
            [(0, 0), (1, 1)],
        ]

        from collections.abc import Callable

        self._turnable_offsets: list[
            list[Callable[[int], tuple[int, int]] | tuple[int, int]]
        ] = [
            [lambda x: (-1, x), (-1, 0), (0, 1)],
            [lambda y: (y, 1), (1, 0), (-1, 0)],
            [lambda x: (1, x), (0, -2), (0, 0)],
            [lambda y: (-y, -1), (-1, 0), (1, 0)],
        ]
        self._render_offsets: list[
            list[Callable[[int], tuple[int, int]]]
        ] = [
            [lambda y: (y - 2, 0), lambda y: (y - 1, 0)],
            [lambda x: (0, 2 - x), lambda x: (0, 1 - x)],
            [lambda y: (2 - y, 0), lambda y: (1 - y, 0)],
            [lambda x: (0, x - 2), lambda x: (0, x - 1)],
        ]

    @property
    def turnable(self) -> bool:
        """Return ``True`` if the S-block can rotate."""
        state = self.tetris.state
        if state == 0 and self.tetris.current_rows[2] == 0:
            return False
        coords = [
            (self.tetris.current_rows[r], self.tetris.current_cols[c])
            for r, c in self._turnable_check_indexes[state]
        ]
        row, col = coords[0]
        offset_func = self._turnable_offsets[state][0]
        assert callable(offset_func)
        for i in range(3):
            oy, ox = offset_func(i)
            if self.tetris.grid[row + oy][col + ox].is_occupied:
                return False
        blocks_to_check = zip(
            coords[1:], self._turnable_offsets[state][1:], strict=False
        )
        for (r, c), off in blocks_to_check:
            assert isinstance(off, tuple)
            oy, ox = off
            if self.tetris.grid[r + oy][c + ox].is_occupied:
                return False
        return True

    def render_background_blocks(self) -> None:
        """Place the S-block cells in the new rotation position."""
        state = self.tetris.state
        coords = [
            (self.tetris.current_rows[r], self.tetris.current_cols[c])
            for r, c in self._render_block_indexes[state]
        ]
        blocks_to_render = zip(
            coords, self._render_offsets[state], [0, 2], strict=False
        )
        for (row, col), offset_func, block_offset in blocks_to_render:
            for i in range(2):
                oy, ox = offset_func(i)
                block = self.tetris.grid[row + oy][col + ox]
                block.number = self.tetris.block_number
                self.tetris.current_blocks[i + block_offset] = block

    def turn(self) -> None:
        """Rotate the S-block if possible."""
        self.tetris.refresh()
        self.tetris.rotate(self)


class BlockT:
    """T-shaped Tetromino — block number 6.

    :param tetris: The game instance this block belongs to.
    """

    SHAPE: ClassVar[list[tuple[int, int]]] = [
        (0, 1),
        (1, 0),
        (1, 1),
        (1, 2),
    ]

    def __init__(self, tetris: TetrisGame) -> None:
        self.number = 6
        self.tetris = tetris

        self._turnable_check_indexes: list[list[tuple[int, int]]] = [
            [(1, 1), (0, 1), (0, 3)],
            [(1, 1), (0, 0), (0, 0)],
            [(1, 3), (0, 0), (0, 0)],
            [(3, 1), (0, 0), (0, 0)],
        ]
        self._render_block_indexes: list[list[tuple[int, int]]] = [
            [(3, 3), (0, 0)],
            [(3, 3), (0, 0)],
            [(3, 3), (2, 0)],
            [(3, 3), (0, 0)],
        ]

        from collections.abc import Callable

        self._turnable_offsets: list[
            list[Callable[[int], tuple[int, int]] | tuple[int, int]]
        ] = [
            [lambda x: (1, x), (0, 0), (0, 0)],
            [lambda y: (y, -1), (-1, 0), (1, 0)],
            [lambda x: (-1, x), (0, -1), (0, 1)],
            [lambda y: (y, 1), (-1, 0), (1, 0)],
        ]
        self._render_offsets: list[
            list[tuple[int, int] | Callable[[int], tuple[int, int]]]
        ] = [
            [(0, 0), lambda y: (y, 0)],
            [(0, 0), lambda x: (0, -x)],
            [(0, 0), lambda y: (1 - y, 0)],
            [(0, 0), lambda x: (0, x)],
        ]

    @property
    def turnable(self) -> bool:
        """Return ``True`` if the T-block can rotate."""
        state = self.tetris.state
        coords = [
            (self.tetris.current_rows[r], self.tetris.current_cols[c])
            for r, c in self._turnable_check_indexes[state]
        ]
        row, col = coords[0]
        offset_func = self._turnable_offsets[state][0]
        assert callable(offset_func)
        for i in range(3):
            oy, ox = offset_func(i)
            if self.tetris.grid[row + oy][col + ox].is_occupied:
                return False
        blocks_to_check = zip(
            coords[1:], self._turnable_offsets[state][1:], strict=False
        )
        for (r, c), off in blocks_to_check:
            assert isinstance(off, tuple)
            oy, ox = off
            if self.tetris.grid[r + oy][c + ox].is_occupied:
                return False
        return True

    def render_background_blocks(self) -> None:
        """Place the T-block cells in the new rotation position."""
        state = self.tetris.state
        (r1, c1), (r2, c2) = self._render_block_indexes[state]
        coords = [
            (self.tetris.current_rows[r], self.tetris.current_cols[c])
            for r, c in self._render_block_indexes[state]
        ]
        row, col = coords[0]
        fixed_off = self._render_offsets[state][0]
        assert isinstance(fixed_off, tuple)
        oy, ox = fixed_off
        block = self.tetris.grid[row + oy][col + ox]
        block.number = self.tetris.block_number
        self.tetris.current_blocks[0] = block

        row, col = coords[1]
        offset_func = self._render_offsets[state][1]
        assert callable(offset_func)
        for i in range(3):
            oy, ox = offset_func(i)
            block = self.tetris.grid[row + oy][col + ox]
            block.number = self.tetris.block_number
            self.tetris.current_blocks[i + 1] = block

    def turn(self) -> None:
        """Rotate the T-block if possible."""
        self.tetris.refresh()
        self.tetris.rotate(self)


class BlockZ:
    """Z-shaped Tetromino — block number 7.

    :param tetris: The game instance this block belongs to.
    """

    SHAPE: ClassVar[list[tuple[int, int]]] = [
        (0, 0),
        (0, 1),
        (1, 1),
        (1, 2),
    ]

    def __init__(self, tetris: TetrisGame) -> None:
        self.number = 7
        self.tetris = tetris

        self._turnable_check_indexes: list[list[tuple[int, int]]] = [
            [(0, 0), (0, 3), (2, 0)],
            [(0, 0), (0, 2), (3, 0)],
            [(0, 3), (0, 3), (2, 0)],
            [(3, 0), (0, 2), (3, 0)],
        ]
        self._render_block_indexes: list[list[tuple[int, int]]] = [
            [(1, 1), (0, 0)],
            [(1, 1), (0, 0)],
            [(1, 1), (0, 0)],
            [(1, 1), (0, 0)],
        ]

        from collections.abc import Callable

        self._turnable_offsets: list[
            list[Callable[[int], tuple[int, int]] | tuple[int, int]]
        ] = [
            [lambda x: (-1, x), (0, 0), (0, 0)],
            [lambda y: (y, 1), (0, 0), (0, 0)],
            [lambda x: (1, x), (0, 0), (0, 0)],
            [lambda y: (y, -1), (0, 0), (0, 0)],
        ]
        self._render_offsets: list[
            list[Callable[[int], tuple[int, int]]]
        ] = [
            [lambda y: (y - 1, 0), lambda y: (y, 0)],
            [lambda x: (0, 1 - x), lambda x: (0, -x)],
            [lambda y: (1 - y, 0), lambda y: (-y, 0)],
            [lambda x: (0, x - 1), lambda x: (0, x)],
        ]

    @property
    def turnable(self) -> bool:
        """Return ``True`` if the Z-block can rotate."""
        state = self.tetris.state
        if state == 0 and self.tetris.current_rows[0] == 0:
            return False
        coords = [
            (self.tetris.current_rows[r], self.tetris.current_cols[c])
            for r, c in self._turnable_check_indexes[state]
        ]
        row, col = coords[0]
        offset_func = self._turnable_offsets[state][0]
        assert callable(offset_func)
        for i in range(3):
            oy, ox = offset_func(i)
            if self.tetris.grid[row + oy][col + ox].is_occupied:
                return False
        blocks_to_check = zip(
            coords[1:], self._turnable_offsets[state][1:], strict=False
        )
        for (r, c), off in blocks_to_check:
            assert isinstance(off, tuple)
            oy, ox = off
            if self.tetris.grid[r + oy][c + ox].is_occupied:
                return False
        return True

    def render_background_blocks(self) -> None:
        """Place the Z-block cells in the new rotation position."""
        state = self.tetris.state
        coords = [
            (self.tetris.current_rows[r], self.tetris.current_cols[c])
            for r, c in self._render_block_indexes[state]
        ]
        blocks_to_render = zip(
            coords, self._render_offsets[state], [0, 2], strict=False
        )
        for (row, col), offset_func, block_offset in blocks_to_render:
            for i in range(2):
                oy, ox = offset_func(i)
                block = self.tetris.grid[row + oy][col + ox]
                block.number = self.tetris.block_number
                self.tetris.current_blocks[i + block_offset] = block

    def turn(self) -> None:
        """Rotate the Z-block if possible."""
        self.tetris.refresh()
        self.tetris.rotate(self)
