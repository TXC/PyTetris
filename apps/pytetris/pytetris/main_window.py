"""Main application window for PyTetris."""

import logging
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtMultimedia import QSoundEffect
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pytetris.controllers.game_controller import GameController
from pytetris.widgets.board_widget import CELL_SIZE, BoardWidget
from pytetris.widgets.next_block_widget import NextBlockWidget

log = logging.getLogger(__name__)

#: Frames per second — determines the QTimer interval.
_FPS: int = 30

#: Milliseconds between each timer tick.
_TICK_MS: int = 1000 // _FPS

#: Resource root relative to this file's location.
_RESOURCES = Path(__file__).parent.parent.parent.parent.parent / "resources"


class MainWindow(QMainWindow):
    """Top-level application window.

    Constructs and lays out all child widgets, creates the
    :class:`~pytetris.controllers.game_controller.GameController`, and wires
    up the game loop timer and sound effects.
    """

    def __init__(self, db_path: Path | None = None) -> None:
        super().__init__()
        if db_path is None:
            db_path = Path(__file__).parent / "HighestScore.sqlite"

        self._controller = GameController(db_path=db_path)
        self._build_ui()
        self._wire_controller()
        self._init_sounds()
        self._start_timer()

    # ------------------------------------------------------------------
    # UI construction (layout only — no business logic)
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        self.setWindowTitle("PyTetris")

        central = QWidget(self)
        self.setCentralWidget(central)

        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # --- Board ---------------------------------------------------------
        self._board = BoardWidget(central)
        root_layout.addWidget(self._board)

        # --- Side panel ----------------------------------------------------
        side = QWidget(central)
        side.setFixedWidth(5 * CELL_SIZE)
        side_layout = QVBoxLayout(side)
        side_layout.setContentsMargins(8, 8, 8, 8)
        side_layout.setSpacing(8)

        self._score_label = QLabel("Score: 0", side)
        self._score_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        side_layout.addWidget(self._score_label)

        self._avg_label = QLabel("Avg: 0.00s", side)
        self._avg_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        side_layout.addWidget(self._avg_label)

        self._best_label = QLabel("Best: —", side)
        self._best_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        side_layout.addWidget(self._best_label)

        side_layout.addSpacing(CELL_SIZE)

        next_label = QLabel("Next:", side)
        side_layout.addWidget(next_label)

        self._next_block_widget = NextBlockWidget(side)
        side_layout.addWidget(self._next_block_widget)

        side_layout.addStretch()

        self._new_game_btn = QPushButton("New Game", side)
        side_layout.addWidget(self._new_game_btn)

        root_layout.addWidget(side)

        self.adjustSize()
        self.setFixedSize(self.sizeHint())

    # ------------------------------------------------------------------
    # Controller wiring
    # ------------------------------------------------------------------

    def _wire_controller(self) -> None:
        c = self._controller

        # Board ← controller
        c.on_board_changed = self._refresh_board
        c.on_block_placed = self._on_block_placed
        c.on_line_cleared = self._on_line_cleared
        c.on_game_over = self._on_game_over

        # Input → controller
        self._board.move_requested.connect(c.handle_key_move)

        # New game button
        self._new_game_btn.clicked.connect(self._on_new_game_clicked)

        # Initialise display
        self._refresh_board()
        self._refresh_best_score()

    def _init_sounds(self) -> None:
        self._sound_place = self._load_sound(
            "202230__deraj__pop-sound.wav", 0.2
        )
        self._sound_erase = self._load_sound(
            "143607__dwoboyle__menu-interface-confirm-003.wav", 0.15
        )
        self._sound_game_over = self._load_sound(
            "42349__irrlicht__game-over.wav", 0.2
        )
        self._sound_music = self._load_sound(
            "580898__bloodpixelhero__in-game.wav", 0.04
        )
        if self._sound_music is not None:
            # QSoundEffect::Infinite = -2 in Qt6 (loop forever).
            self._sound_music.setLoopCount(-2)
            self._sound_music.play()

    def _start_timer(self) -> None:
        self._timer = QTimer(self)
        self._timer.setInterval(_TICK_MS)
        self._timer.timeout.connect(self._controller.tick)
        self._timer.start()

    # ------------------------------------------------------------------
    # Slots (called by controller callbacks — UI concerns only)
    # ------------------------------------------------------------------

    def _refresh_board(self) -> None:
        """Push current game state to the board and side-panel widgets."""
        c = self._controller
        self._board.set_grid(c.game.grid)
        self._score_label.setText(f"Score: {c.game.score}")
        self._avg_label.setText(f"Avg: {c.avg_time:.2f}s")
        self._next_block_widget.set_block(c.next_block)

    def _on_block_placed(self) -> None:
        if self._sound_place is not None:
            self._sound_place.play()

    def _on_line_cleared(self, lines: int) -> None:
        if self._sound_erase is not None:
            self._sound_erase.play()

    def _on_game_over(self, score: int, avg_time: float) -> None:
        self._timer.stop()
        if self._sound_music is not None:
            self._sound_music.stop()
        if self._sound_game_over is not None:
            self._sound_game_over.play()
        self._refresh_best_score()
        self._board.update()

    def _on_new_game_clicked(self) -> None:
        self._timer.stop()
        if self._sound_music is not None:
            self._sound_music.stop()
        self._controller.new_game()
        self._refresh_board()
        self._refresh_best_score()
        self._timer.start()
        if self._sound_music is not None:
            self._sound_music.play()

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------

    def _refresh_best_score(self) -> None:
        scores = self._controller.high_scores()
        if scores:
            best_score, best_avg = scores[0]
            self._best_label.setText(
                f"Best: {best_score} / {best_avg:.2f}s"
            )

    @staticmethod
    def _load_sound(filename: str, volume: float) -> QSoundEffect | None:
        """Load a WAV file as a :class:`QSoundEffect`.

        :param filename: Filename relative to ``resources/audio/``.
        :param volume: Linear volume in [0.0, 1.0].
        :return: Loaded effect, or ``None`` if the file is not found.
        """
        path = _RESOURCES / "audio" / filename
        if not path.exists():
            log.warning("Audio file not found: %s", path)
            return None
        effect = QSoundEffect()
        effect.setSource(QUrl.fromLocalFile(str(path)))
        effect.setVolume(volume)
        return effect
