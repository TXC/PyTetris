"""SQLite persistence for PyTetris high-score data."""

import sqlite3
from pathlib import Path

_SCHEMA = "CREATE TABLE HighestScore (Score INTEGER, AverageTimeToPutABlock REAL)"
_SEED = "INSERT INTO HighestScore (Score, AverageTimeToPutABlock) VALUES (0, 0)"


class DB:
    """SQLite-backed high-score store.

    Creates the database file (and schema) on first use if it does not already
    exist.  The connection is left open for the lifetime of this object.

    :param path: Filesystem path to the SQLite database file.
    """

    def __init__(self, path: Path) -> None:
        create = not path.exists()
        self._con = sqlite3.connect(str(path))
        self._cur = self._con.cursor()
        if create:
            self._cur.execute(_SCHEMA)
            self._cur.execute(_SEED)
            self._con.commit()

    def fetch_highest_score(self) -> list[tuple[int, float]]:
        """Return all score records, ordered by score descending.

        :return: List of ``(score, avg_time)`` tuples.
        :rtype: list[tuple[int, float]]
        """
        self._cur.execute(
            "SELECT Score, AverageTimeToPutABlock "
            "FROM HighestScore ORDER BY Score DESC"
        )
        rows: list[tuple[int, float]] = self._cur.fetchall()
        return rows

    def save_highest_score(self, score: int, avg_time: float) -> None:
        """Persist a new score entry.

        :param score: Game score to record.
        :param avg_time: Average seconds per block placement.
        """
        self._cur.execute(
            "INSERT INTO HighestScore VALUES (?, ?)",
            (score, avg_time),
        )
        self._con.commit()

    def close(self) -> None:
        """Close the underlying database connection."""
        self._con.close()
