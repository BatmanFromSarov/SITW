import io
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import app
from sitw.core import Assistant as PublicAssistant
from sitw.core.assistant import Assistant
from sitw.core.ollama_backend import OllamaBackend
from sitw.database.storage import Storage


class CliIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / "data" / "sitw.db"
        patcher = patch("sitw.database.storage.__file__", str(Path(self.tmp.name) / "sitw/database/storage.py"))
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_cli(self, inputs, argv=None):
        out, err = io.StringIO(), io.StringIO()
        with patch("builtins.input", side_effect=inputs), patch("sys.stdout", out), patch("sys.stderr", err):
            status = app.main([] if argv is None else argv)
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

    def test_default_and_explicit_test_backend_never_create_ollama(self):
        for argv in ([], ["--backend", "test"],
                     ["--model", "other:7b", "--timeout", "2.5"]):
            with self.subTest(argv=argv), patch("app.OllamaBackend") as factory:
                status, out, err = self.run_cli(["hello", "exit"], argv)
                self.assertEqual(status, 0)
                self.assertEqual(err, "")
                self.assertIn("SITW получил сообщение: hello", out)
                factory.assert_not_called()

    def test_ollama_selection_and_configuration(self):
        for extra, model, timeout in (([], "qwen2.5:7b", 120.0),
                                     (["--model", "other:7b", "--timeout", "2.5"], "other:7b", 2.5)):
            with self.subTest(extra=extra), patch("app.OllamaBackend") as factory:
                factory.return_value = Mock(spec=OllamaBackend)
                factory.return_value.generate_chat.return_value = "answer"
                status, out, err = self.run_cli(["hello", "exit"], ["--backend", "ollama"] + extra)
                self.assertEqual(status, 0)
                self.assertEqual(err, "")
                self.assertIn("SITW: answer", out)
                factory.assert_called_once_with(model=model, timeout=timeout)
                factory.return_value.generate_chat.assert_called_once_with([
                    {"role": "user", "content": "hello"}
                ] if not extra else [
                    {"role": "user", "content": "hello"},
                    {"role": "assistant", "content": "answer"},
                    {"role": "user", "content": "hello"},
                ])
                factory.return_value.close.assert_called_once_with()

    def test_invalid_arguments_fail_before_opening_resources(self):
        cases = [["--backend", "unknown"], ["--model", ""], ["--model", "   "],
                 ["--unknown"], ["--model"], ["--timeout"], ["--backend"]]
        cases.extend(["--timeout", value] for value in ("0", "-1", "nan", "inf", "-inf", "abc"))
        cases.extend(["--context-messages", value] for value in ("0", "-1", "1.5", "abc"))
        for argv in cases:
            with self.subTest(argv=argv), patch("app.Storage") as storage, patch("app.OllamaBackend") as backend:
                with patch("sys.stderr", io.StringIO()), self.assertRaises(SystemExit) as caught:
                    app.main(argv)
                self.assertEqual(caught.exception.code, 2)
                storage.assert_not_called()
                backend.assert_not_called()

    def test_help_exits_without_opening_resources(self):
        with patch("app.Storage") as storage, patch("app.OllamaBackend") as backend:
            with patch("sys.stdout", io.StringIO()) as out, self.assertRaises(SystemExit) as caught:
                app.main(["--help"])
            self.assertEqual(caught.exception.code, 0)
            for flag in ("--backend", "--model", "--timeout", "--context-messages"):
                self.assertIn(flag, out.getvalue())
            storage.assert_not_called()
            backend.assert_not_called()

    def test_ollama_http_success_persistence_order_and_restart(self):
        with patch("sitw.core.ollama_backend.HTTPConnection") as factory:
            response = MagicMock()
            response.__enter__.return_value = response
            response.status = 200
            response.read.return_value = b'{"message":{"role":"assistant","content":"answer"},"done":true}'
            factory.return_value.getresponse.return_value = response

            def check_saved_user(*args, **kwargs):
                store = Storage()
                try:
                    self.assertEqual([(m["role"], m["content"]) for m in store.get_history()],
                                     [("user", "hello")])
                finally:
                    store.close()

            factory.return_value.request.side_effect = check_saved_user
            status, out, err = self.run_cli(["hello", "exit"], ["--backend", "ollama"])
            self.assertEqual((status, err), (0, ""))
            self.assertIn("SITW: answer", out)
            payload = json.loads(factory.return_value.request.call_args.kwargs["body"])
            self.assertEqual(payload, {"model": "qwen2.5:7b", "messages": [{"role": "user", "content": "hello"}], "stream": False})
            factory.return_value.close.assert_called_once_with()
            response.__exit__.assert_called_once()
        store = Storage()
        try:
            self.assertEqual([(m["role"], m["content"]) for m in store.get_history()],
                             [("user", "hello"), ("assistant", "answer")])
        finally:
            store.close()
        status, out, err = self.run_cli(["exit"], ["--backend", "ollama"])
        self.assertEqual((status, err), (0, ""))
        self.assertIn("Восстановлена история (2 сообщений)", out)

    def test_ollama_http_failures_keep_user_and_close_resources(self):
        cases = [(ConnectionRefusedError("private detail"), 200, b""),
                 (TimeoutError("private detail"), 200, b""),
                 (None, 500, b"private detail"),
                 (None, 200, b"private detail"),
                 (None, 200, b'{"error":"private detail"}'),
                 (None, 200, b'{"response":" ","done":true}')]
        for failure, status_code, body in cases:
            with self.subTest(failure=failure, status=status_code, body=body), patch(
                "sitw.core.ollama_backend.HTTPConnection"
            ) as factory:
                response = MagicMock()
                response.__enter__.return_value = response
                response.status = status_code
                response.read.return_value = body
                factory.return_value.getresponse.return_value = response
                factory.return_value.request.side_effect = failure
                store = Storage()
                with patch("app.Storage", return_value=store):
                    status, out, err = self.run_cli(["failed message"], ["--backend", "ollama"])
                self.assertEqual(status, 1)
                self.assertIn("Ваше сообщение сохранено", err)
                self.assertNotIn("private detail", out + err)
                self.assertNotIn("Traceback", out + err)
                factory.return_value.close.assert_called_once_with()
                factory.return_value.request.assert_called_once()
                with self.assertRaises(sqlite3.ProgrammingError):
                    store.get_history()
        reopened = Storage()
        try:
            self.assertEqual([(m["role"], m["content"]) for m in reopened.get_history()],
                             [("user", "failed message")] * len(cases))
        finally:
            reopened.close()
        status, out, err = self.run_cli(["exit"])
        self.assertEqual((status, err), (0, ""))
        self.assertIn(f"Восстановлена история ({len(cases)} сообщений)", out)

    def test_chat_restart_limit_pending_users_and_no_duplicate_current(self):
        with patch("sitw.core.ollama_backend.HTTPConnection") as factory:
            response = MagicMock()
            response.__enter__.return_value = response
            response.status = 200
            response.read.return_value = (
                b'{"message":{"role":"assistant","content":"reply"},"done":true}'
            )
            factory.return_value.getresponse.return_value = response
            argv = ["--backend", "ollama"]
            self.assertEqual(self.run_cli(["same", "exit"], argv)[0], 0)
            # A new main invocation creates a new Storage, Assistant and backend.
            self.assertEqual(self.run_cli(["same", "exit"], argv)[0], 0)
            payload = json.loads(factory.return_value.request.call_args.kwargs["body"])
            self.assertEqual(factory.return_value.request.call_args.args, ("POST", "/api/chat"))
            self.assertEqual(payload, {"model": "qwen2.5:7b", "stream": False,
                "messages": [
                    {"role": "user", "content": "same"},
                    {"role": "assistant", "content": "reply"},
                    {"role": "user", "content": "same"},
                ]})
            factory.return_value.request.side_effect = ConnectionRefusedError("private")
            calls_before = factory.return_value.request.call_count
            self.assertEqual(self.run_cli(["pending"], argv)[0], 1)
            self.assertEqual(factory.return_value.request.call_count, calls_before + 1)
            store = Storage()
            try:
                before = store.get_history()
                self.assertEqual(before[-1]["role"], "user")
                self.assertEqual(len(before), 5)
            finally:
                store.close()
            factory.return_value.request.side_effect = None
            # Last three records: orphan assistant, pending user, current user.
            self.assertEqual(self.run_cli(["current", "exit"],
                                         argv + ["--context-messages", "3"])[0], 0)
            self.assertEqual(json.loads(factory.return_value.request.call_args.kwargs["body"])["messages"], [
                {"role": "user", "content": "pending"},
                {"role": "user", "content": "current"},
            ])
            store = Storage()
            try:
                after = store.get_history()
                self.assertEqual(after[:5], before)
                self.assertEqual(len(after), 7)
            finally:
                store.close()
            self.assertEqual(self.run_cli(["only", "exit"],
                                         argv + ["--context-messages", "1"])[0], 0)
            self.assertEqual(json.loads(factory.return_value.request.call_args.kwargs["body"])["messages"], [
                {"role": "user", "content": "only"},
            ])

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
