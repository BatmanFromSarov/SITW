import json
import unittest
from http.client import HTTPException, IncompleteRead, RemoteDisconnected
from unittest.mock import MagicMock, patch

from sitw.core.assistant import Assistant
from sitw.core.backend import GenerationError, InvalidResponseError, TextBackend
from sitw.core.backend import ModelUnavailableError, ResponseInterruptedError, ServerUnavailableError
from sitw.core.ollama_backend import OllamaBackend


class OllamaBackendTests(unittest.TestCase):
    def setUp(self):
        patcher = patch("sitw.core.ollama_backend.HTTPConnection")
        self.connection_type = patcher.start()
        self.addCleanup(patcher.stop)
        self.connection = self.connection_type.return_value
        self.response = MagicMock()
        self.response.__enter__.return_value = self.response
        self.connection.getresponse.return_value = self.response
        self.response.status = 200
        self.set_response({"message": {"role": "assistant", "content": " Ответ\n"}, "done": True})
        self.backend: TextBackend = OllamaBackend()
        self.addCleanup(self.backend.close)

    def set_response(self, value):
        self.response.read.return_value = json.dumps(value, ensure_ascii=False).encode("utf-8")

    def test_default_request_and_unicode_response(self):
        self.assertEqual(self.backend.generate("Привет"), " Ответ\n")
        self.connection_type.assert_called_once_with("127.0.0.1", 11434, timeout=120.0)
        args, kwargs = self.connection.request.call_args
        self.assertEqual(args, ("POST", "/api/chat"))
        self.assertEqual(json.loads(kwargs["body"].decode("utf-8")), {
            "model": "qwen2.5:7b", "messages": [{"role": "user", "content": "Привет"}], "stream": False,
        })
        self.assertEqual(kwargs["headers"]["Content-Type"], "application/json")
        self.response.__exit__.assert_called_once()
        self.connection.close.assert_called_once_with()

    def test_custom_model_and_timeout(self):
        backend = OllamaBackend(model="other:7b", timeout=5)
        self.addCleanup(backend.close)
        backend.generate("hello")
        self.connection_type.assert_called_once_with("127.0.0.1", 11434, timeout=5)
        self.assertEqual(json.loads(self.connection.request.call_args.kwargs["body"])["model"], "other:7b")

    def test_rejects_invalid_configuration_before_http(self):
        for model in (None, "", " \n", 123):
            with self.subTest(model=model), self.assertRaises(ValueError):
                OllamaBackend(model=model)
        for timeout in (None, 0, -1, True, "5", float("inf"), float("nan")):
            with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                OllamaBackend(timeout=timeout)
        self.connection_type.assert_not_called()

    def test_http_errors_do_not_expose_or_read_server_body(self):
        for status in (301, 400, 404, 500, 503):
            with self.subTest(status=status):
                self.response.status = status
                self.response.read.reset_mock()
                with self.assertRaises(GenerationError) as caught:
                    self.backend.generate("hello")
                self.assertNotIn(str(status), str(caught.exception))
                self.response.read.assert_not_called()
        self.assertEqual(self.connection.close.call_count, 5)
        self.assertEqual(self.response.__exit__.call_count, 5)

    def test_failure_types_and_response_cleanup(self):
        cases = [
            (self.connection.request, ConnectionRefusedError("private detail"), ServerUnavailableError, False),
            (self.connection.request, BrokenPipeError("private detail"), ResponseInterruptedError, False),
            (self.connection.getresponse, RemoteDisconnected("private detail"), ResponseInterruptedError, False),
            (self.response.read, IncompleteRead(b"private detail"), ResponseInterruptedError, True),
            (self.response.read, ConnectionResetError("private detail"), ResponseInterruptedError, True),
            (self.response.read, TimeoutError("private detail"), GenerationError, True),
        ]
        for stage, failure, expected, entered in cases:
            with self.subTest(failure=type(failure).__name__, stage=stage):
                self.connection.close.reset_mock()
                self.response.__exit__.reset_mock()
                stage.side_effect = failure
                try:
                    with self.assertRaises(expected) as caught:
                        self.backend.generate("hello")
                    self.assertIs(type(caught.exception), expected)
                    self.assertNotIn("private detail", str(caught.exception))
                    self.assertTrue(caught.exception.__suppress_context__)
                    self.connection.close.assert_called_once_with()
                    self.assertEqual(self.response.__exit__.call_count, int(entered))
                finally:
                    stage.side_effect = None

    def test_missing_model_has_distinct_error_and_closes_response(self):
        self.response.status = 404
        with self.assertRaises(ModelUnavailableError):
            self.backend.generate("hello")
        self.response.read.assert_not_called()
        self.response.__exit__.assert_called_once()
        self.connection.close.assert_called_once_with()

    def test_transport_failures_are_safe_and_connections_close(self):
        for stage in (self.connection.request, self.connection.getresponse, self.response.read):
            for failure in (ConnectionRefusedError("private detail"), TimeoutError("private detail"),
                            HTTPException("private detail"), IncompleteRead(b"private detail")):
                with self.subTest(stage=stage, failure=type(failure).__name__):
                    stage.side_effect = failure
                    self.connection.close.reset_mock()
                    with self.assertRaises(GenerationError) as caught:
                        self.backend.generate("hello")
                    self.assertNotIn("private detail", str(caught.exception))
                    self.assertTrue(caught.exception.__suppress_context__)
                    self.connection.close.assert_called_once_with()
                    stage.side_effect = None

    def test_invalid_json_and_encoding(self):
        for raw in (b"", b"not json private detail", b"\xff", b'{"response":',
                    b'{"response":"a"}\n{"response":"b"}'):
            with self.subTest(raw=raw):
                self.response.read.return_value = raw
                with self.assertRaises(InvalidResponseError) as caught:
                    self.backend.generate("hello")
                self.assertNotIn("private detail", str(caught.exception))
        self.assertEqual(self.connection.close.call_count, 5)

    def test_empty_nontext_and_incomplete_responses(self):
        values = [None, [], "text", 42, {}, {"response": "answer"},
                  {"response": "answer", "done": False}, {"response": "answer", "done": 1}]
        values.extend({"response": text, "done": True}
                      for text in ("", " \t\n", None, 123, False, [], {}))
        values.extend({"message": message, "done": True} for message in (
            None, [], "answer", {}, {"role": "user", "content": "answer"},
            {"role": "assistant"},
        ))
        values.extend({"message": {"role": "assistant", "content": text}, "done": True}
                      for text in ("", " \t\n", None, 123, False, [], {}))
        values.extend({"message": {"role": "assistant", "content": "answer"}, "done": done}
                      for done in (False, None, 1))
        for value in values:
            with self.subTest(value=value):
                self.set_response(value)
                with self.assertRaises(InvalidResponseError):
                    self.backend.generate("hello")
        self.assertEqual(self.connection.close.call_count, len(values))

    def test_api_error_does_not_expose_details(self):
        self.set_response({"error": "private model path", "response": "answer", "done": True})
        with self.assertRaises(GenerationError) as caught:
            self.backend.generate("hello")
        self.assertNotIn("private model path", str(caught.exception))
        self.connection.close.assert_called_once_with()
        self.response.__exit__.assert_called_once()

    def test_each_call_sends_only_current_message(self):
        self.backend.generate("first")
        self.backend.generate("second")
        payloads = [json.loads(call.kwargs["body"]) for call in self.connection.request.call_args_list]
        self.assertEqual(payloads, [
            {"model": "qwen2.5:7b", "messages": [{"role": "user", "content": message}], "stream": False}
            for message in ("first", "second")
        ])
        self.assertEqual(self.connection_type.call_count, 2)
        self.assertEqual(self.connection.close.call_count, 2)

    def test_explicit_chat_preserves_roles_order_and_strips_metadata(self):
        self.backend.generate_chat([
            {"role": "user", "content": "first", "id": 1},
            {"role": "assistant", "content": "reply"},
            {"role": "user", "content": "pending"},
            {"role": "user", "content": "first"},
        ])
        self.assertEqual(json.loads(self.connection.request.call_args.kwargs["body"]), {
            "model": "qwen2.5:7b", "stream": False, "messages": [
                {"role": "user", "content": "first"},
                {"role": "assistant", "content": "reply"},
                {"role": "user", "content": "pending"},
                {"role": "user", "content": "first"},
            ],
        })

    def test_invalid_chat_fails_before_http(self):
        for messages in ([], [None], [{"role": "system", "content": "text"}],
                         [{"role": "user", "content": " "}],
                         [{"role": "assistant", "content": "reply"}]):
            with self.subTest(messages=messages), self.assertRaises(GenerationError):
                self.backend.generate_chat(messages)
        self.connection_type.assert_not_called()

    def test_close_is_idempotent_and_prevents_http(self):
        self.backend.close()
        self.backend.close()
        with self.assertRaises(GenerationError):
            self.backend.generate("hello")
        self.connection_type.assert_not_called()

    def test_assistant_accepts_backend_and_owns_lifecycle(self):
        assistant = Assistant(self.backend)
        self.assertEqual(assistant.respond("hello"), " Ответ\n")
        assistant.close()
        with self.assertRaises(GenerationError):
            self.backend.generate("hello")
        self.assertEqual(self.connection_type.call_count, 1)


if __name__ == "__main__":
    unittest.main()
