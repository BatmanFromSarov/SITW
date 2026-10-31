import io
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app
from sitw.core import Assistant as PublicAssistant
from sitw.core.assistant import Assistant
from sitw.database.storage import Storage


class CliIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / "data" / "sitw.db"
        patcher = patch("sitw.database.storage.__file__", str(Path(self.tmp.name) / "sitw/database/storage.py"))
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_cli(self, inputs):
        out, err = io.StringIO(), io.StringIO()
        with patch("builtins.input", side_effect=inputs), patch("sys.stdout", out), patch("sys.stderr", err):
            status = app.main()
        return status, out.getvalue(), err.getvalue()

    def test_two_runs_keep_order_without_duplicates(self):
        self.assertEqual(self.run_cli(["первое", "второе", "exit"])[0], 0)
        status, output, _ = self.run_cli(["третье", "exit"])
        self.assertEqual(status, 0)
        self.assertIn("Восстановлена история (4 сообщений)", output)
        store = Storage()
        try:
            history = store.get_history()
            self.assertEqual([(m["role"], m["content"]) for m in history], [
                ("user", "первое"), ("assistant", "SITW получил сообщение: первое"),
                ("user", "второе"), ("assistant", "SITW получил сообщение: второе"),
                ("user", "третье"), ("assistant", "SITW получил сообщение: третье"),
            ])
        finally:
            store.close()

    def test_user_write_failure_stops_before_response(self):
        real = Storage.save_message
        def fail_user(self, role, content):
            if role == "user":
                raise sqlite3.OperationalError("injected user failure")
            return real(self, role, content)
        with patch.object(Storage, "save_message", fail_user):
            status, _, err = self.run_cli(["hello"])
        self.assertEqual(status, 1)
        self.assertIn("injected user failure", err)
        store = Storage()
        try:
            self.assertEqual(store.get_history(), [])
        finally:
            store.close()

    def test_assistant_write_failure_keeps_user_message(self):
        real = Storage.save_message
        def fail_assistant(self, role, content):
            if role == "assistant":
                raise sqlite3.OperationalError("injected assistant failure")
            return real(self, role, content)
        with patch.object(Storage, "save_message", fail_assistant):
            status, out, err = self.run_cli(["hello"])
        self.assertEqual(status, 1)
        self.assertIn("injected assistant failure", err)
        self.assertNotIn("SITW: SITW получил сообщение", out)
        status, _, _ = self.run_cli(["exit"])
        self.assertEqual(status, 0)
        store = Storage()
        try:
            self.assertEqual([(m["role"], m["content"]) for m in store.get_history()], [("user", "hello")])
        finally:
            store.close()

    def test_repeated_empty_run_does_not_modify_history(self):
        self.run_cli(["hello", "exit"])
        before = self.db.read_bytes()
        self.run_cli(["exit"])
        self.assertEqual(self.db.read_bytes(), before)

    def test_imports_share_single_assistant(self):
        self.assertIs(PublicAssistant, Assistant)


if __name__ == "__main__":
    unittest.main()
