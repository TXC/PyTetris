"""Tests for pytetris_core.game — TetrisGame engine."""

from pathlib import Path

import pytest
from pytetris_core.blocks import (
    BlockI,
    BlockJ,
    BlockL,
    BlockO,
    BlockS,
    BlockT,
    BlockZ,
)
from pytetris_core.db import DB
from pytetris_core.game import COLS, ROWS, TetrisGame
from pytetris_core.models import BackgroundBlock, Move
from pytetris_core.time_tracking import TimeTracking

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def game() -> TetrisGame:
    """Return a freshly initialised :class:`TetrisGame`."""
    return TetrisGame()


@pytest.fixture()
def started_j(game: TetrisGame) -> tuple[TetrisGame, BlockJ]:
    """Return a game with a J-block already spawned."""
    block = BlockJ(game)
    game.start(block)
    return game, block


# ---------------------------------------------------------------------------
# Grid initialisation
# ---------------------------------------------------------------------------


class TestGridInit:
    def test_grid_dimensions(self, game: TetrisGame) -> None:
        assert len(game.grid) == ROWS
        assert all(len(row) == COLS for row in game.grid)

    def test_left_wall_is_occupied(self, game: TetrisGame) -> None:
        for row in range(ROWS):
            assert game.grid[row][0].is_occupied
            assert game.grid[row][0].number == 8

    def test_right_wall_is_occupied(self, game: TetrisGame) -> None:
        for row in range(ROWS):
            assert game.grid[row][COLS - 1].is_occupied

    def test_floor_is_occupied(self, game: TetrisGame) -> None:
        for col in range(COLS):
            assert game.grid[ROWS - 1][col].is_occupied

    def test_interior_cells_are_empty(self, game: TetrisGame) -> None:
        for row in range(ROWS - 1):
            for col in range(1, COLS - 1):
                cell = game.grid[row][col]
                assert not cell.is_occupied
                assert cell.number == 0

    def test_cell_coordinates_match_position(self, game: TetrisGame) -> None:
        for row in range(ROWS):
            for col in range(COLS):
                assert game.grid[row][col].row == row
                assert game.grid[row][col].col == col


# ---------------------------------------------------------------------------
# State property
# ---------------------------------------------------------------------------


class TestState:
    def test_initial_state_is_zero(self, game: TetrisGame) -> None:
        assert game.state == 0

    def test_state_wraps_forward(self, game: TetrisGame) -> None:
        game.state = 4
        assert game.state == 0

    def test_state_wraps_backward(self, game: TetrisGame) -> None:
        game.state = -1
        assert game.state == 3

    @pytest.mark.parametrize("value", [0, 1, 2, 3])
    def test_valid_states_accepted(
        self, game: TetrisGame, value: int
    ) -> None:
        game.state = value
        assert game.state == value


# ---------------------------------------------------------------------------
# start()
# ---------------------------------------------------------------------------


class TestStart:
    def test_start_j_places_block_at_row0(
        self, started_j: tuple[TetrisGame, BlockJ]
    ) -> None:
        game, _ = started_j
        assert game.grid[0][4].number == 2

    def test_start_sets_block_number(
        self, started_j: tuple[TetrisGame, BlockJ]
    ) -> None:
        game, _ = started_j
        assert game.block_number == 2

    def test_start_increments_block_count(self, game: TetrisGame) -> None:
        block = BlockJ(game)
        game.start(block)
        assert game.number_of_blocks == 1

    def test_start_resets_state(self, game: TetrisGame) -> None:
        game._state = 2
        game.start(BlockJ(game))
        assert game.state == 0

    def test_start_sets_gameover_when_spawn_occupied(
        self, game: TetrisGame
    ) -> None:
        # Fill spawn positions with a placed block.
        for col in range(4, 8):
            game.grid[0][col].number = 1
            game.grid[0][col].is_occupied = True
        game.start(BlockI(game))
        assert game.game_over

    def test_start_i_places_four_cells_in_row0(
        self, game: TetrisGame
    ) -> None:
        game.start(BlockI(game))
        occupied = [
            game.grid[0][col].number
            for col in range(4, 8)
        ]
        assert occupied == [1, 1, 1, 1]


# ---------------------------------------------------------------------------
# go() — horizontal movement
# ---------------------------------------------------------------------------


class TestGoHorizontal:
    def test_go_left_moves_block(
        self, started_j: tuple[TetrisGame, BlockJ]
    ) -> None:
        game, _ = started_j
        game.go(Move.LEFT)
        # J spawns with cell at [0][4]; after moving left it should be at col 3.
        assert game.grid[0][3].number == 2

    def test_go_right_moves_block(
        self, started_j: tuple[TetrisGame, BlockJ]
    ) -> None:
        game, _ = started_j
        game.go(Move.RIGHT)
        assert game.grid[0][5].number == 2

    def test_go_left_blocked_by_wall(self, game: TetrisGame) -> None:
        # Place a J-block as close to the left wall as possible.
        game.start(BlockJ(game))
        for _ in range(4):
            game.go(Move.LEFT)
        # Further left moves should be blocked — the block stays put.
        before = game.grid[0][1].number
        game.go(Move.LEFT)
        assert game.grid[0][1].number == before

    def test_go_returns_none_for_horizontal_moves(
        self, started_j: tuple[TetrisGame, BlockJ]
    ) -> None:
        game, _ = started_j
        assert game.go(Move.LEFT) is None
        assert game.go(Move.RIGHT) is None


# ---------------------------------------------------------------------------
# go() — downward movement
# ---------------------------------------------------------------------------


class TestGoDown:
    def test_go_down_moves_block_one_row(
        self, started_j: tuple[TetrisGame, BlockJ]
    ) -> None:
        game, _ = started_j
        game.go(Move.DOWN)
        assert game.grid[2][4].number == 2

    def test_go_down_returns_none_when_still_falling(
        self, started_j: tuple[TetrisGame, BlockJ]
    ) -> None:
        game, _ = started_j
        result = game.go(Move.DOWN)
        assert result is None

    def test_go_down_returns_row_list_when_placed(
        self, started_j: tuple[TetrisGame, BlockJ]
    ) -> None:
        game, _ = started_j
        result = None
        for _ in range(19):
            result = game.go(Move.DOWN)
        assert isinstance(result, list)
        assert all(isinstance(r, int) for r in result)

    def test_block_is_occupied_after_placement(
        self, started_j: tuple[TetrisGame, BlockJ]
    ) -> None:
        game, _ = started_j
        for _ in range(19):
            game.go(Move.DOWN)
        # Cells at the bottom must be marked as occupied.
        assert game.grid[19][5].is_occupied or game.grid[19][4].is_occupied

    def test_current_blocks_cleared_after_placement(
        self, started_j: tuple[TetrisGame, BlockJ]
    ) -> None:
        game, _ = started_j
        for _ in range(19):
            game.go(Move.DOWN)
        assert len(game.current_blocks) == 0


# ---------------------------------------------------------------------------
# Line clearing
# ---------------------------------------------------------------------------


class TestLineClearing:
    def _fill_row(self, game: TetrisGame, row: int) -> None:
        for col in range(1, COLS - 1):
            game.grid[row][col].number = 1
            game.grid[row][col].is_occupied = True

    def test_score_increases_by_100_per_cleared_line(
        self, game: TetrisGame
    ) -> None:
        self._fill_row(game, 18)
        # Leave one gap so the engine can detect the row via placed_rows.
        game.grid[18][5].is_occupied = True
        game._erase_complete_lines([18])
        assert game.score == 100

    def test_cleared_row_becomes_empty(self, game: TetrisGame) -> None:
        self._fill_row(game, 18)
        game._erase_complete_lines([18])
        for col in range(1, COLS - 1):
            assert not game.grid[18][col].is_occupied
            assert game.grid[18][col].number == 0

    def test_rows_above_shift_down(self, game: TetrisGame) -> None:
        self._fill_row(game, 18)
        game.grid[17][5].number = 3
        game.grid[17][5].is_occupied = True
        game._erase_complete_lines([18])
        # The marker block should have shifted from row 17 to row 18.
        assert game.grid[18][5].number == 3

    def test_two_simultaneous_lines_score_200(
        self, game: TetrisGame
    ) -> None:
        self._fill_row(game, 17)
        self._fill_row(game, 18)
        game._erase_complete_lines([17, 18])
        assert game.score == 200


# ---------------------------------------------------------------------------
# refresh()
# ---------------------------------------------------------------------------


class TestRefresh:
    def test_refresh_populates_current_rows_and_cols(
        self, started_j: tuple[TetrisGame, BlockJ]
    ) -> None:
        game, _ = started_j
        game.refresh()
        assert len(game.current_rows) == 4
        assert len(game.current_cols) == 4

    def test_refresh_rows_match_current_blocks(
        self, started_j: tuple[TetrisGame, BlockJ]
    ) -> None:
        game, _ = started_j
        game.refresh()
        for i, block in enumerate(game.current_blocks):
            assert game.current_rows[i] == block.row

    def test_refresh_cols_match_current_blocks(
        self, started_j: tuple[TetrisGame, BlockJ]
    ) -> None:
        game, _ = started_j
        game.refresh()
        for i, block in enumerate(game.current_blocks):
            assert game.current_cols[i] == block.col


# ---------------------------------------------------------------------------
# BackgroundBlock
# ---------------------------------------------------------------------------


class TestBackgroundBlock:
    def test_fields_stored_correctly(self) -> None:
        b = BackgroundBlock(col=3, row=5, number=2, is_occupied=True)
        assert b.col == 3
        assert b.row == 5
        assert b.number == 2
        assert b.is_occupied is True

    def test_default_mutable(self) -> None:
        b = BackgroundBlock(col=1, row=1, number=0, is_occupied=False)
        b.number = 7
        assert b.number == 7


# ---------------------------------------------------------------------------
# TimeTracking
# ---------------------------------------------------------------------------


class TestTimeTracking:
    def test_initial_values_are_zero(self) -> None:
        ti = TimeTracking()
        assert ti.avg_time == 0.0
        assert ti.total_time == 0.0

    def test_update_time_calculates_average(self) -> None:
        ti = TimeTracking()
        ti.start_time = 0.0
        ti.update_time(2.0, 1)
        assert ti.avg_time == pytest.approx(2.0)
        assert ti.total_time == pytest.approx(2.0)

    def test_update_time_running_average(self) -> None:
        ti = TimeTracking()
        ti.start_time = 0.0
        ti.update_time(4.0, 1)  # 4 s for block 1
        ti.start_time = 4.0
        ti.update_time(6.0, 2)  # 2 s for block 2 → avg = 3 s
        assert ti.avg_time == pytest.approx(3.0)

    def test_update_time_raises_for_zero_block_count(self) -> None:
        ti = TimeTracking()
        with pytest.raises(ValueError):
            ti.update_time(1.0, 0)


# ---------------------------------------------------------------------------
# DB
# ---------------------------------------------------------------------------


class TestDB:
    def test_creates_db_and_returns_seed_row(self, tmp_path: Path) -> None:
        db = DB(tmp_path / "scores.sqlite")
        rows = db.fetch_highest_score()
        assert len(rows) >= 1
        db.close()

    def test_save_and_fetch_score(self, tmp_path: Path) -> None:
        db = DB(tmp_path / "scores.sqlite")
        db.save_highest_score(500, 1.5)
        rows = db.fetch_highest_score()
        scores = [r[0] for r in rows]
        assert 500 in scores
        db.close()

    def test_fetch_ordered_by_score_desc(self, tmp_path: Path) -> None:
        db = DB(tmp_path / "scores.sqlite")
        db.save_highest_score(100, 2.0)
        db.save_highest_score(800, 1.0)
        db.save_highest_score(300, 1.5)
        rows = db.fetch_highest_score()
        scores = [r[0] for r in rows]
        assert scores == sorted(scores, reverse=True)
        db.close()


# ---------------------------------------------------------------------------
# Block shapes
# ---------------------------------------------------------------------------


class TestBlockShapes:
    @pytest.mark.parametrize(
        "block_cls",
        [BlockI, BlockJ, BlockL, BlockO, BlockS, BlockT, BlockZ],
    )
    def test_shape_has_four_cells(
        self, block_cls: type, game: TetrisGame
    ) -> None:
        assert len(block_cls.SHAPE) == 4

    @pytest.mark.parametrize(
        "block_cls, expected_number",
        [
            (BlockI, 1),
            (BlockJ, 2),
            (BlockL, 3),
            (BlockO, 4),
            (BlockS, 5),
            (BlockT, 6),
            (BlockZ, 7),
        ],
    )
    def test_block_numbers(
        self,
        block_cls: type,
        expected_number: int,
        game: TetrisGame,
    ) -> None:
        block = block_cls(game)
        assert block.number == expected_number
