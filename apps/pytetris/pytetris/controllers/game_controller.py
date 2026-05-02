"""Game controller for the PyTetris application.

This module contains only plain Python — no Qt imports.  The controller
orchestrates the :class:`~pytetris_core.game.TetrisGame` engine and notifies
the application layer via simple callbacks.
"""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from pathlib import Path

from pytetris_core.blocks import (
    Block,
    BlockI,
    BlockJ,
    BlockL,
    BlockO,
    BlockS,
    BlockT,
    BlockZ,
)
from pytetris_core.db import DB
from pytetris_core.game import TetrisGame
from pytetris_core.models import Move
from pytetris_core.time_tracking import TimeTracking

_BlockFactory = Callable[[TetrisGame], Block]

_BLOCK_CLASSES: list[_BlockFactory] = [
    BlockI,
    BlockJ,
    BlockL,
    BlockO,
    BlockS,
    BlockT,
    BlockZ,
]

#: Number of :meth:`tick` calls between automatic descents.
DESCENT_EVERY: int = 20


class GameController:
    """Orchestrates a :class:`~pytetris_core.game.TetrisGame` session.

    The controller drives block spawning, the descent timer, user-input
    handling, and score persistence.  It communicates with the view layer
    exclusively through the four callable attributes listed below — the view
    assigns them; the controller calls them.

    :param db_path: Path to the SQLite high-score database.
    """

    def __init__(self, db_path: Path) -> None:
        self._db = DB(db_path)
        self._ti = TimeTracking()
        self._descent_counter: int = 0

        # Callbacks — replace with view handlers.
        self.on_board_changed: Callable[[], None] = lambda: None
        self.on_block_placed: Callable[[], None] = lambda: None
        self.on_line_cleared: Callable[[int], None] = lambda _lines: None
        self.on_game_over: Callable[[int, float], None] = (
            lambda _score, _avg: None
        )

        self.game = TetrisGame()
        self.current_block: Block = self._random_block()
        self.next_block: Block = self._random_block()
        self._spawn_current()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def new_game(self) -> None:
        """Reset and start a fresh game session."""
        self.game = TetrisGame()
        self._ti = TimeTracking()
        self._descent_counter = 0
        self.current_block = self._random_block()
        self.next_block = self._random_block()
        self._spawn_current()
        self.on_board_changed()

    def tick(self) -> None:
        """Advance one frame of the game loop.

        Called periodically by a :class:`~PyQt6.QtCore.QTimer` in the view.
        Descends the current block every :data:`DESCENT_EVERY` ticks.
        """
        if self.game.game_over:
            return
        self._descent_counter += 1
        if self._descent_counter % DESCENT_EVERY == 0:
            self._try_descend()
        self.on_board_changed()

    def handle_key_move(self, move: Move) -> None:
        """React to a directional key press from the player.

        :param move: The movement direction requested.
        """
        if self.game.game_over:
            return
        if move == Move.UP:
            self.current_block.turn()
        elif move == Move.DOWN:
            self._descent_counter = 0
            self._try_descend()
        else:
            self.game.go(move)
        self.on_board_changed()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _random_block(self) -> Block:
        cls: _BlockFactory = random.choice(_BLOCK_CLASSES)
        return cls(self.game)

    def _spawn_current(self) -> None:
        """Spawn :attr:`current_block` and advance the block queue."""
        self._ti.start_time = time.time()
        self.game.start(self.current_block)

    def _try_descend(self) -> None:
        """Move the block down one row; handle placement if it lands."""
        score_before = self.game.score
        result = self.game.go(Move.DOWN)
        if result is not None:
            self._on_block_landed(result, score_before)

    def _on_block_landed(
        self, placed_rows: list[int], score_before: int
    ) -> None:
        """Handle a block landing: update timing, advance queue, check game over.

        Spawning the next block may set :attr:`~TetrisGame.game_over`, so the
        game-over check is deliberately placed *after* the spawn attempt.
        """
        self._ti.update_time(time.time(), self.game.number_of_blocks)
        self.on_block_placed()

        lines_cleared = self._count_lines_above(placed_rows, score_before)
        if lines_cleared > 0:
            self.on_line_cleared(lines_cleared)

        # Advance the block queue and attempt to spawn the next piece.
        self.current_block = self.next_block
        self.next_block = self._random_block()
        self._spawn_current()

        # Game-over is set by start() when the spawn area is occupied.
        if self.game.game_over:
            self._db.save_highest_score(self.game.score, self._ti.avg_time)
            self.on_game_over(self.game.score, self._ti.avg_time)

    def _count_lines_above(
        self, placed_rows: list[int], score_before: int
    ) -> int:
        """Return how many complete lines were cleared after placing.

        :param placed_rows: Row indices of just-placed block cells (unused
            directly — score delta is the reliable indicator).
        :param score_before: :attr:`~TetrisGame.score` value *before* the
            block landed.
        :return: Number of lines cleared.
        """
        return (self.game.score - score_before) // 100

    def high_scores(self) -> list[tuple[int, float]]:
        """Return the stored high-score records, best first.

        :return: List of ``(score, avg_time_seconds)`` tuples.
        :rtype: list[tuple[int, float]]
        """
        return self._db.fetch_highest_score()

    @property
    def avg_time(self) -> float:
        """Current running average block-placement time in seconds."""
        return self._ti.avg_time
