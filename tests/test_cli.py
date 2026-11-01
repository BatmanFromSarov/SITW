import io
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

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

    def test_backend_success_is_persisted_and_resources_closed(self):
        backend = Mock()
        backend.generate.return_value = "generated answer"
        assistant = Assistant(backend)
        store = Storage()
        with patch("app.Assistant", return_value=assistant), patch("app.Storage", return_value=store):
            status, out, err = self.run_cli(["hello", "exit"])
        self.assertEqual(status, 0)
        self.assertEqual(err, "")
        self.assertIn("SITW: generated answer", out)
        backend.close.assert_called_once_with()
        with self.assertRaises(sqlite3.ProgrammingError):
            store.get_history()
        reopened = Storage()
        try:
            self.assertEqual([(m["role"], m["content"]) for m in reopened.get_history()],
                             [("user", "hello"), ("assistant", "generated answer")])
        finally:
            reopened.close()

    def check_generation_failure(self, backend, reason):
        assistant = Assistant(backend)
        store = Storage()
        with patch("app.Assistant", return_value=assistant), patch("app.Storage", return_value=store):
            status, out, err = self.run_cli(["failed message"])
        self.assertEqual(status, 1)
        self.assertIn(reason, err)
        self.assertIn("Ваше сообщение сохранено", err)
        self.assertNotIn("SITW: SITW получил", out)
        backend.close.assert_called_once_with()
        with self.assertRaises(sqlite3.ProgrammingError):
            store.get_history()
        return store

    def test_backend_exception_keeps_user_and_history_recovers(self):
        self.run_cli(["before", "exit"])
        backend = Mock()
        backend.generate.side_effect = OSError("private backend detail")
        self.check_generation_failure(backend, "сбой backend")
        status, out, err = self.run_cli(["after", "exit"])
        self.assertEqual(status, 0)
        self.assertEqual(err, "")
        self.assertIn("Восстановлена история (3 сообщений)", out)
        store = Storage()
        try:
            self.assertEqual([(m["role"], m["content"]) for m in store.get_history()], [
                ("user", "before"), ("assistant", "SITW получил сообщение: before"),
                ("user", "failed message"),
                ("user", "after"), ("assistant", "SITW получил сообщение: after"),
            ])
        finally:
            store.close()

    def test_empty_backend_response_is_not_saved(self):
        backend = Mock()
        backend.generate.return_value = " \n\t"
        self.check_generation_failure(backend, "пустой или некорректный ответ")
        self.assert_only_failed_user_saved()

    def test_nontext_backend_response_is_not_saved(self):
        backend = Mock()
        backend.generate.return_value = None
        self.check_generation_failure(backend, "пустой или некорректный ответ")
        self.assert_only_failed_user_saved()

    def assert_only_failed_user_saved(self):
        store = Storage()
        try:
            self.assertEqual([(m["role"], m["content"]) for m in store.get_history()],
                             [("user", "failed message")])
        finally:
            store.close()

    def test_backend_cleanup_failure_still_closes_storage(self):
        backend = Mock()
        backend.generate.side_effect = RuntimeError("generation failed")
        backend.close.side_effect = RuntimeError("cleanup failed")
        assistant = Assistant(backend)
        store = Storage()
        with patch("app.Assistant", return_value=assistant), patch("app.Storage", return_value=store):
            status, _, err = self.run_cli(["hello"])
        self.assertEqual(status, 1)
        self.assertIn("Не удалось сформировать ответ", err)
        self.assertIn("Ошибка освобождения ресурсов backend", err)
        with self.assertRaises(sqlite3.ProgrammingError):
            store.get_history()

    def test_storage_error_closes_backend(self):
        backend = Mock()
        with patch("app.Assistant", return_value=Assistant(backend)), patch.object(
            Storage, "get_history", side_effect=sqlite3.OperationalError("read failed")
        ):
            status, _, err = self.run_cli([])
        self.assertEqual(status, 1)
        self.assertIn("read failed", err)
        backend.close.assert_called_once_with()

    def test_eof_and_keyboard_interrupt_close_backend(self):
        for interrupt in (EOFError(), KeyboardInterrupt()):
            with self.subTest(interrupt=type(interrupt).__name__):
                backend = Mock()
                with patch("app.Assistant", return_value=Assistant(backend)):
                    status, _, err = self.run_cli([interrupt])
                self.assertEqual(status, 0)
                self.assertEqual(err, "")
                backend.close.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
