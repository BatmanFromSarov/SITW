"""Independent Ollama chat adapter using only the standard library."""

import json
import math
from http.client import HTTPConnection, HTTPException, IncompleteRead

from .backend import (
    GenerationError, InvalidResponseError, ModelUnavailableError,
    ResponseInterruptedError, ServerUnavailableError,
)


class OllamaBackend:
    """TextBackend with optional explicit history for http://127.0.0.1:11434.

    Each generate call owns and closes its HTTP connection. timeout is a
    socket-operation timeout in seconds, not a total generation deadline.
    close is idempotent; it neither stops Ollama nor unloads its model.
    """

    def __init__(self, model: str = "qwen2.5:7b", timeout: float = 120.0) -> None:
        if not isinstance(model, str) or not model.strip():
            raise ValueError("Model must be nonblank text")
        if (
            isinstance(timeout, bool)
            or not isinstance(timeout, (int, float))
            or not math.isfinite(timeout)
            or timeout <= 0
        ):
            raise ValueError("Timeout must be a positive finite number")
        self._model = model
        self._timeout = timeout
        self._closed = False

    def generate(self, message: str) -> str:
        return self.generate_chat([{"role": "user", "content": message}])

    def generate_chat(self, messages: list[dict[str, str]]) -> str:
        if self._closed:
            raise GenerationError("Локальная модель отключена.")
        if not messages or any(
            not isinstance(item, dict)
            or item.get("role") not in ("user", "assistant")
            or not isinstance(item.get("content"), str)
            or not item["content"].strip()
            for item in messages
        ) or messages[-1]["role"] != "user":
            raise GenerationError("Некорректный контекст диалога.")
        payload = [{"role": item["role"], "content": item["content"]} for item in messages]
        body = json.dumps(
            {"model": self._model, "messages": payload, "stream": False},
            ensure_ascii=False,
        ).encode("utf-8")
        connection = HTTPConnection("127.0.0.1", 11434, timeout=self._timeout)
        try:
            connection.request(
                "POST", "/api/chat", body=body,
                headers={"Content-Type": "application/json", "Accept": "application/json"},
            )
            with connection.getresponse() as response:
                if response.status == 404:
                    raise ModelUnavailableError("Запрошенная модель недоступна.")
                if response.status != 200:
                    raise GenerationError("Локальная модель не смогла сформировать ответ.")
                raw = response.read()
        except ConnectionRefusedError:
            raise ServerUnavailableError("Не удалось подключиться к Ollama.") from None
        except (ConnectionError, IncompleteRead):
            raise ResponseInterruptedError("Получение ответа прервано.") from None
        except (OSError, HTTPException):
            raise GenerationError("Не удалось получить ответ от локальной модели.") from None
        finally:
            connection.close()

        try:
            result = json.loads(raw.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            raise InvalidResponseError("Локальная модель вернула некорректный ответ.") from None
        if not isinstance(result, dict):
            raise InvalidResponseError("Локальная модель вернула некорректный ответ.")
        if "error" in result:
            raise GenerationError("Локальная модель не смогла сформировать ответ.")
        reply = result.get("message")
        if not isinstance(reply, dict) or reply.get("role") != "assistant":
            raise InvalidResponseError("Локальная модель вернула некорректный ответ.")
        text = reply.get("content")
        if not isinstance(text, str) or not text.strip() or result.get("done") is not True:
            raise InvalidResponseError("Локальная модель вернула пустой или незавершённый ответ.")
        return text

    def close(self) -> None:
        """Disable future calls; connections are already closed by generate."""
        self._closed = True
