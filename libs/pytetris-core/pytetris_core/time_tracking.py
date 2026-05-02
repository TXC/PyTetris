"""Time-tracking utilities for the PyTetris game."""


class TimeTracking:
    """Track placement timing statistics during a Tetris game.

    Computes the running average time (in seconds) that the player takes to
    place each block.
    """

    def __init__(self) -> None:
        self.avg_time: float = 0.0
        self.total_time: float = 0.0
        self.start_time: float = 0.0

    def update_time(self, current_time: float, block_count: int) -> None:
        """Record that a block was placed and recompute the running average.

        :param current_time: Wall-clock time at placement (seconds, e.g. from
            ``time.time()``).
        :param block_count: Total number of blocks placed so far (must be ≥ 1).
        :raises ValueError: If ``block_count`` is less than 1.
        """
        if block_count < 1:
            raise ValueError(
                f"block_count must be at least 1, got {block_count}"
            )
        self.total_time += current_time - self.start_time
        self.avg_time = self.total_time / block_count
