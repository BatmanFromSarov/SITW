"""Independent, single-message Ollama adapter using only the standard library."""

import json
import math
from http.client import HTTPConnection, HTTPException

from .backend import GenerationError, InvalidResponseError


class OllamaBackend:
    """TextBackend for http://127.0.0.1:11434, without dialogue history.

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
        if self._closed:
            raise GenerationError("Локальная модель отключена.")
        body = json.dumps(
            {"model": self._model, "prompt": message, "stream": False},
            ensure_ascii=False,
        ).encode("utf-8")
        connection = HTTPConnection("127.0.0.1", 11434, timeout=self._timeout)
        try:
            connection.request(
                "POST", "/api/generate", body=body,
                headers={"Content-Type": "application/json", "Accept": "application/json"},
            )
            with connection.getresponse() as response:
                if response.status != 200:
                    raise GenerationError("Локальная модель не смогла сформировать ответ.")
                raw = response.read()
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
        text = result.get("response")
        if not isinstance(text, str) or not text.strip() or result.get("done") is not True:
            raise InvalidResponseError("Локальная модель вернула пустой или незавершённый ответ.")
        return text

    def close(self) -> None:
        """Disable future calls; connections are already closed by generate."""
        self._closed = True
