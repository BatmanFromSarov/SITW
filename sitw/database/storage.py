"""Minimal persistent SQLite message storage for SITW CLI."""

import sqlite3
from pathlib import Path


class Storage:
    def __init__(self) -> None:
        db_path = Path(__file__).resolve().parents[2] / "data" / "sitw.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(db_path)
        try:
            with self._connection:
                self._connection.execute(
                    """CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
                    )"""
                )
        except Exception:
            self._connection.close()
            raise

    def save_message(self, role: str, content: str) -> None:
        if role not in ("user", "assistant"):
            raise ValueError("role must be 'user' or 'assistant'")
        with self._connection:
            self._connection.execute(
                "INSERT INTO messages (role, content) VALUES (?, ?)", (role, content)
            )

    def get_history(self) -> list[dict]:
        rows = self._connection.execute(
            "SELECT id, role, content, created_at FROM messages ORDER BY id ASC"
        ).fetchall()
        return [
            {"id": row[0], "role": row[1], "content": row[2], "created_at": row[3]}
            for row in rows
        ]

    def close(self) -> None:
        self._connection.close()
