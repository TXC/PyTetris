"""Tests for pytetris.controllers.game_controller — plain Python, no Qt."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytetris_core.models import Move

from pytetris.controllers.game_controller import GameController

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "scores.sqlite"


@pytest.fixture()
def controller(db_path: Path) -> GameController:
    """Return a freshly created :class:`GameController`."""
    return GameController(db_path=db_path)


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------


class TestInit:
    def test_game_is_not_over_on_start(
        self, controller: GameController
    ) -> None:
        assert not controller.game.game_over

    def test_score_is_zero_on_start(
        self, controller: GameController
    ) -> None:
        assert controller.game.score == 0

    def test_next_block_is_set(self, controller: GameController) -> None:
        # A block must be queued after construction.
        assert controller.next_block is not None

    def test_current_block_is_set(self, controller: GameController) -> None:
        assert controller.current_block is not None


# ---------------------------------------------------------------------------
# new_game()
# ---------------------------------------------------------------------------


class TestNewGame:
    def test_new_game_resets_score(self, controller: GameController) -> None:
        controller.game.score = 500
        controller.new_game()
        assert controller.game.score == 0

    def test_new_game_resets_game_over(
        self, controller: GameController
    ) -> None:
        controller.game.game_over = True
        controller.new_game()
        assert not controller.game.game_over

    def test_new_game_calls_board_changed(
        self, controller: GameController
    ) -> None:
        cb = MagicMock()
        controller.on_board_changed = cb
        controller.new_game()
        assert cb.called


# ---------------------------------------------------------------------------
# handle_key_move()
# ---------------------------------------------------------------------------


class TestHandleKeyMove:
    def test_left_key_does_not_raise(
        self, controller: GameController
    ) -> None:
        controller.handle_key_move(Move.LEFT)

    def test_right_key_does_not_raise(
        self, controller: GameController
    ) -> None:
        controller.handle_key_move(Move.RIGHT)

    def test_down_key_does_not_raise(
        self, controller: GameController
    ) -> None:
        controller.handle_key_move(Move.DOWN)

    def test_rotate_key_does_not_raise(
        self, controller: GameController
    ) -> None:
        controller.handle_key_move(Move.UP)

    def test_key_move_triggers_board_changed(
        self, controller: GameController
    ) -> None:
        cb = MagicMock()
        controller.on_board_changed = cb
        controller.handle_key_move(Move.LEFT)
        assert cb.called

    def test_key_ignored_when_game_over(
        self, controller: GameController
    ) -> None:
        controller.game.game_over = True
        cb = MagicMock()
        controller.on_board_changed = cb
        controller.handle_key_move(Move.LEFT)
        cb.assert_not_called()


# ---------------------------------------------------------------------------
# tick()
# ---------------------------------------------------------------------------


class TestTick:
    def test_tick_triggers_board_changed(
        self, controller: GameController
    ) -> None:
        cb = MagicMock()
        controller.on_board_changed = cb
        controller.tick()
        assert cb.called

    def test_tick_does_nothing_when_game_over(
        self, controller: GameController
    ) -> None:
        controller.game.game_over = True
        cb = MagicMock()
        controller.on_board_changed = cb
        controller.tick()
        cb.assert_not_called()

    def test_block_placed_callback_fires_on_landing(
        self, controller: GameController
    ) -> None:
        """Force immediate descent to trigger block placement."""
        cb = MagicMock()
        controller.on_block_placed = cb
        # Drop the block all the way down to the floor.
        for _ in range(20):
            controller.handle_key_move(Move.DOWN)
        assert cb.called

    def test_game_over_callback_fires(
        self, db_path: Path
    ) -> None:
        controller = GameController(db_path=db_path)
        over_cb = MagicMock()
        controller.on_game_over = over_cb
        # Move the current block away from the spawn area first.
        for _ in range(5):
            controller.handle_key_move(Move.DOWN)
        # Fill rows 0 and 1 completely so any block type triggers game over.
        for row in range(2):
            for col in range(1, 11):
                controller.game.grid[row][col].number = 1
                controller.game.grid[row][col].is_occupied = True
        # Drop the rest of the way to the floor to trigger spawn + game over.
        for _ in range(20):
            controller.handle_key_move(Move.DOWN)
        assert over_cb.called


# ---------------------------------------------------------------------------
# Callbacks are no-ops by default
# ---------------------------------------------------------------------------


class TestDefaultCallbacks:
    def test_default_on_board_changed_is_callable(
        self, controller: GameController
    ) -> None:
        controller.on_board_changed()  # must not raise

    def test_default_on_block_placed_is_callable(
        self, controller: GameController
    ) -> None:
        controller.on_block_placed()  # must not raise

    def test_default_on_line_cleared_is_callable(
        self, controller: GameController
    ) -> None:
        controller.on_line_cleared(1)  # must not raise

    def test_default_on_game_over_is_callable(
        self, controller: GameController
    ) -> None:
        controller.on_game_over(0, 0.0)  # must not raise
