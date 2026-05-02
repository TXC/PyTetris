"""Tetris game engine — pure Python, no display framework dependencies."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from .models import BackgroundBlock, Move

if TYPE_CHECKING:
    from .blocks import Block

#: Number of columns in the play field (including left/right walls).
COLS: int = 12
#: Number of rows in the play field (including the floor row).
ROWS: int = 21


def _init_grid() -> list[list[BackgroundBlock]]:
    grid: list[list[BackgroundBlock]] = []
    for row in range(ROWS):
        grid_row: list[BackgroundBlock] = []
        for col in range(COLS):
            is_wall = col in (0, COLS - 1) or row == ROWS - 1
            grid_row.append(
                BackgroundBlock(
                    col=col,
                    row=row,
                    number=8 if is_wall else 0,
                    is_occupied=is_wall,
                )
            )
        grid.append(grid_row)
    return grid


class TetrisGame:
    """Core Tetris game engine.

    Owns the game grid and tracks the active piece, score, and rotation state.
    All coordinate values are in *grid units* — the caller decides how many
    pixels each cell occupies.

    The engine is deliberately side-effect-free with respect to rendering: it
    only manipulates the :class:`~pytetris_core.models.BackgroundBlock` data
    model.  Callers are responsible for reading the model and drawing it.

    :raises RuntimeError: If :meth:`start` is called before the grid is
        populated with a valid block.
    """

    def __init__(self) -> None:
        self.score: int = 0
        self.game_over: bool = False
        self.number_of_blocks: int = 0
        self.block_number: int = 0
        #: Snapshot of the grid cells where the *next* block would land
        #: (used for game-over detection).
        self.next_blocks: list[int] = []
        #: The four :class:`BackgroundBlock` cells occupied by the moving piece.
        self.current_blocks: list[BackgroundBlock] = []
        #: Row index for each cell in :attr:`current_blocks`.
        self.current_rows: list[int] = []
        #: Column index for each cell in :attr:`current_blocks`.
        self.current_cols: list[int] = []
        self._state: int = 0
        #: The full 21×12 game grid.
        self.grid: list[list[BackgroundBlock]] = _init_grid()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def state(self) -> int:
        """Current rotation state (0–3)."""
        return self._state

    @state.setter
    def state(self, value: int) -> None:
        """Set rotation state, wrapping around [0, 3]."""
        if value > 3:
            self._state = 0
        elif value < 0:
            self._state = 3
        else:
            self._state = value

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self, block: Block) -> None:
        """Spawn *block* at the top of the play field.

        Updates :attr:`current_blocks`, sets :attr:`game_over` if the spawn
        position is already occupied, and resets the rotation :attr:`state`.

        :param block: The block instance to spawn.
        """
        self.block_number = block.number
        self.number_of_blocks += 1

        _Grid = list[list[BackgroundBlock]]
        _Fetcher = Callable[[_Grid], list[BackgroundBlock]]
        fetch_blocks_map: list[_Fetcher] = [
            lambda g: g[0][4:8],  # I
            lambda g: [g[0][4], *g[1][4:7]],  # J
            lambda g: [*g[1][4:7], g[0][6]],  # L
            lambda g: [b for row in g[0:2] for b in row[5:7]],  # O
            lambda g: [*g[1][4:6], *g[0][5:7]],  # S
            lambda g: [g[0][5], *g[1][4:7]],  # T
            lambda g: [*g[0][4:6], *g[1][5:7]],  # Z
        ]
        fetcher = fetch_blocks_map[self.block_number - 1]
        spawn_cells = fetcher(self.grid)

        self.next_blocks.clear()
        self.next_blocks.extend(cell.number for cell in spawn_cells)
        self.game_over = any(n in range(1, 8) for n in self.next_blocks)
        if self.game_over:
            return

        self.current_blocks.clear()
        for cell in spawn_cells:
            cell.number = self.block_number
            self.current_blocks.append(cell)

        self._state = 0

    def go(self, move: Move) -> list[int] | None:
        """Apply *move* to the active piece.

        For :attr:`~Move.LEFT` / :attr:`~Move.RIGHT` moves the piece one cell
        horizontally if the destination is free.

        For :attr:`~Move.DOWN` the piece descends one row.  If the row below
        is occupied the piece is *placed*: each cell is marked as occupied and
        the method returns the **row indices** of the placed cells so the
        caller can check for completed lines.  If the piece continues moving,
        ``None`` is returned.

        :param move: The direction to move.
        :return: List of row indices where the piece was placed, or ``None``
            if the piece is still in motion.
        """
        self.next_blocks.clear()

        if move in (Move.LEFT, Move.RIGHT):
            adjust = -1 if move == Move.LEFT else 1
            for i in range(4):
                nb = self.grid[self.current_blocks[i].row][
                    self.current_blocks[i].col + adjust
                ]
                self.next_blocks.append(nb.number)
                if nb.number in range(1, 9) and nb.is_occupied:
                    return None
            self._move_horizontally(adjust)
            return None

        # Move.DOWN
        for i in range(4):
            nb = self.grid[self.current_blocks[i].row + 1][
                self.current_blocks[i].col
            ]
            self.next_blocks.append(nb.number)
            if nb.number in range(1, 9) and nb.is_occupied:
                placed_rows = []
                for j in range(4):
                    self.current_blocks[j].is_occupied = True
                    placed_rows.append(self.current_blocks[j].row)
                self.current_blocks.clear()
                self._erase_complete_lines(placed_rows)
                return placed_rows

        self._clear_current()
        for i in range(4):
            self.current_blocks[i] = self.grid[
                self.current_blocks[i].row + 1
            ][self.current_blocks[i].col]
            self.current_blocks[i].number = self.block_number
        return None

    def rotate(self, block: Block) -> None:
        """Rotate *block* if its :attr:`~blocks.Block.turnable` check passes.

        :param block: The block to rotate.
        """
        if not block.turnable:
            return
        self._clear_current()
        block.render_background_blocks()
        self.state += 1

    def refresh(self) -> None:
        """Rebuild :attr:`current_rows` / :attr:`current_cols` from
        :attr:`current_blocks`.

        Must be called before the ``turnable`` check inside a block's
        ``turn()`` method.
        """
        self.current_rows.clear()
        self.current_cols.clear()
        for block in self.current_blocks:
            self.current_rows.append(block.row)
            self.current_cols.append(block.col)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _clear_current(self) -> None:
        """Reset the number of each cell occupied by the active piece."""
        for block in self.current_blocks:
            block.number = 0

    def _move_horizontally(self, adjust: int) -> None:
        """Shift the active piece left (adjust=-1) or right (adjust=1)."""
        self._clear_current()
        for i in range(4):
            self.current_blocks[i] = self.grid[self.current_blocks[i].row][
                self.current_blocks[i].col + adjust
            ]
            self.current_blocks[i].number = self.block_number

    def _erase_complete_lines(self, placed_rows: list[int]) -> None:
        """Check for and erase any full lines intersecting *placed_rows*.

        After erasing a row, everything above shifts down so the same index is
        rechecked before moving upward.

        :param placed_rows: Row indices of the just-placed block cells.
        """
        max_row = max(placed_rows)
        min_row = min(placed_rows) - 1
        row = max_row
        while row > min_row:
            if self._is_row_full(row):
                self._erase_row(row)
                self.score += 100
                min_row += 1
                # max_row += 1
                # Do NOT decrement row: the same index now contains the row
                # that was directly above, which may also be full.
            else:
                row -= 1

    def _is_row_full(self, row: int) -> bool:
        return all(
            self.grid[row][col].is_occupied
            for col in range(1, COLS - 1)
        )

    def _erase_row(self, row: int) -> None:
        """Clear *row* and shift all rows above it down by one."""
        for col in range(1, COLS - 1):
            self.grid[row][col].is_occupied = False
            self.grid[row][col].number = 0
        for r in range(row, 0, -1):
            for col in range(1, COLS - 1):
                self.grid[r][col].is_occupied = self.grid[r - 1][col].is_occupied
                self.grid[r][col].number = self.grid[r - 1][col].number
                self.grid[r - 1][col].is_occupied = False
                self.grid[r - 1][col].number = 0
