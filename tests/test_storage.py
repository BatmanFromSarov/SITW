import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sitw.database.storage import Storage


class StorageTests(unittest.TestCase):
    def test_limited_history_is_ordered_read_only_and_validated(self):
        store = Storage()
        self.addCleanup(store.close)
        for role, text in (("user", "first"), ("assistant", "reply"),
                           ("user", "pending"), ("user", "current")):
            store.save_message(role, text)
        before = store.get_history()
        db_before = self.db_path.read_bytes()
        schema_before = store._connection.execute(
            "SELECT sql FROM sqlite_master ORDER BY name"
        ).fetchall()
        self.assertEqual(store.get_history(limit=3), before[-3:])
        self.assertEqual(store.get_history(limit=1), before[-1:])
        self.assertEqual(store.get_history(limit=100), before)
        for limit in (0, -1, True, 1.5, "2"):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                store.get_history(limit=limit)
        self.assertEqual(store.get_history(), before)
        self.assertEqual(self.db_path.read_bytes(), db_before)
        self.assertEqual(store._connection.execute(
            "SELECT sql FROM sqlite_master ORDER BY name"
        ).fetchall(), schema_before)
        self.assertEqual(store._connection.execute("PRAGMA integrity_check").fetchone(), ("ok",))

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db_path = Path(self.tmp.name) / "data" / "sitw.db"
        self.file_patch = patch(
            "sitw.database.storage.__file__",
            str(Path(self.tmp.name) / "sitw" / "database" / "storage.py"),
        )
        self.file_patch.start()
        self.addCleanup(self.file_patch.stop)

    def test_creates_database_and_returns_ordered_records(self):
        store = Storage()
        self.assertTrue(self.db_path.is_file())
        store.save_message("user", "first")
        store.save_message("assistant", "second")
        history = store.get_history()
        self.assertEqual([item["content"] for item in history], ["first", "second"])
        self.assertEqual(list(history[0]), ["id", "role", "content", "created_at"])
        self.assertLess(history[0]["id"], history[1]["id"])
        store.close()

    def test_reopen_keeps_existing_messages(self):
        store = Storage()
        store.save_message("user", "persistent")
        store.close()
        again = Storage()
        self.assertEqual([m["content"] for m in again.get_history()], ["persistent"])
        again.close()

    def test_failed_write_is_reported(self):
        store = Storage()
        store.close()
        with self.assertRaises(sqlite3.ProgrammingError):
            store.save_message("user", "not saved")

    def test_rejects_invalid_role(self):
        store = Storage()
        with self.assertRaises(ValueError):
            store.save_message("system", "not supported")
        self.assertEqual(store.get_history(), [])
        store.close()


if __name__ == "__main__":
    unittest.main()
