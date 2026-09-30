"""Thread-safe SQLite connection management. Single file, WAL mode."""
from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from ..config import settings
from .schema import SCHEMA_SQL


class Database:
    """Thread-safe SQLite wrapper."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = threading.Lock()
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(SCHEMA_SQL)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path, timeout=30)
        conn.row_factory = sqlite3.Row
        # Foreign-key enforcement is connection-local, not a schema setting (#30).
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    @contextmanager
    def write(self) -> Iterator[sqlite3.Connection]:
        """Serialized transaction: state-machine transitions must be atomic."""
        with self._lock:
            with self._connect() as conn:
                # Lock before reading state, including across independent processes (#26).
                conn.execute("BEGIN IMMEDIATE")
                yield conn

    @contextmanager
    def read(self) -> Iterator[sqlite3.Connection]:
        with self._connect() as conn:
            yield conn


db = Database(settings.db_path)
