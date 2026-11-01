import unittest
from unittest.mock import Mock

from sitw.core.assistant import Assistant
from sitw.core.backend import BackendCloseError, GenerationError, InvalidResponseError


class AssistantTests(unittest.TestCase):
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
