import unittest
from unittest.mock import Mock

from sitw.core.assistant import Assistant
from sitw.core.backend import BackendCloseError, GenerationError, InvalidResponseError


class AssistantTests(unittest.TestCase):
    def test_chat_trims_only_leading_assistants_and_keeps_pending_users(self):
        class Chat:
            def generate(self, message):
                raise AssertionError("Expected chat")

            def generate_chat(self, messages):
                self.messages = messages
                return "answer"

            def close(self):
                pass

        backend = Chat()
        assistant = Assistant(backend)
        self.addCleanup(assistant.close)
        history = [
            {"role": "assistant", "content": "old reply"},
            {"role": "assistant", "content": "another reply"},
            {"role": "user", "content": "pending", "id": 3},
            {"role": "user", "content": "current", "id": 4},
        ]
        self.assertEqual(assistant.respond("current", history=history), "answer")
        self.assertEqual(backend.messages, [
            {"role": "user", "content": "pending"},
            {"role": "user", "content": "current"},
        ])
        self.assertEqual(len(history), 4)

    def test_history_preserves_legacy_backend_contract(self):
        class Legacy:
            def generate(self, message):
                return "legacy: " + message

            def close(self):
                pass

        for backend, expected in ((Legacy(), "legacy: hello"),
                                  (None, "SITW получил сообщение: hello")):
            assistant = Assistant(backend)
            try:
                self.assertEqual(assistant.respond("hello", history=[
                    {"role": "user", "content": "hello"}
                ]), expected)
            finally:
                assistant.close()

    def test_default_response_is_compatible(self):
        assistant = Assistant()
        self.addCleanup(assistant.close)
        self.assertEqual(assistant.respond("hello"), "SITW получил сообщение: hello")

    def test_backend_receives_message_and_returns_text_unchanged(self):
        backend = Mock()
        backend.generate.return_value = " ответ \n"
        assistant = Assistant(backend)
        self.addCleanup(assistant.close)
        self.assertEqual(assistant.respond("hello"), " ответ \n")
        backend.generate.assert_called_once_with("hello")

    def test_backend_exception_is_wrapped_with_cause(self):
        backend = Mock()
        failure = OSError("inference failed")
        backend.generate.side_effect = failure
        assistant = Assistant(backend)
        self.addCleanup(assistant.close)
        with self.assertRaises(GenerationError) as caught:
            assistant.respond("hello")
        self.assertIs(caught.exception.__cause__, failure)

    def test_typed_generation_error_is_preserved(self):
        backend = Mock()
        failure = GenerationError("unavailable")
        backend.generate.side_effect = failure
        assistant = Assistant(backend)
        self.addCleanup(assistant.close)
        with self.assertRaises(GenerationError) as caught:
            assistant.respond("hello")
        self.assertIs(caught.exception, failure)

    def test_rejects_empty_and_nontext_results(self):
        backend = Mock()
        assistant = Assistant(backend)
        self.addCleanup(assistant.close)
        for response in ("", " \t\n", None, 123, False, [], {}, b"text"):
            with self.subTest(response=response):
                backend.generate.return_value = response
                with self.assertRaises(InvalidResponseError):
                    assistant.respond("hello")

    def test_close_is_idempotent_and_prevents_generation(self):
        backend = Mock()
        assistant = Assistant(backend)
        assistant.close()
        assistant.close()
        backend.close.assert_called_once_with()
        with self.assertRaises(GenerationError):
            assistant.respond("hello")
        backend.generate.assert_not_called()

    def test_cleanup_failure_is_distinct_and_can_be_retried(self):
        backend = Mock()
        backend.close.side_effect = [RuntimeError("cleanup failed"), None]
        assistant = Assistant(backend)
        with self.assertRaises(BackendCloseError) as caught:
            assistant.close()
        self.assertIsInstance(caught.exception.__cause__, RuntimeError)
        assistant.close()
        self.assertEqual(backend.close.call_count, 2)
