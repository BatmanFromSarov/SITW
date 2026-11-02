from .backend import (
    BackendCloseError,
    ChatBackend,
    GenerationError,
    InvalidResponseError,
    TestBackend,
    TextBackend,
)


class Assistant:
    def __init__(self, backend: TextBackend | None = None) -> None:
        self._backend = backend if backend is not None else TestBackend()
        self._closed = False

    def respond(self, message: str, history: list[dict] | None = None) -> str:
        """history, when supplied, already includes the saved current message."""
        if self._closed:
            raise GenerationError("Assistant is closed")
        try:
            if history is not None and isinstance(self._backend, ChatBackend):
                messages = [{"role": item["role"], "content": item["content"]}
                            for item in history]
                # A bounded window may begin with replies to an omitted user.
                start = 0
                while start < len(messages) and messages[start]["role"] == "assistant":
                    start += 1
                response = self._backend.generate_chat(messages[start:])
            else:
                response = self._backend.generate(message)
        except GenerationError:
            raise
        except Exception as exc:
            raise GenerationError("Backend generation failed") from exc
        if not isinstance(response, str) or not response.strip():
            raise InvalidResponseError("Backend must return nonblank text")
        return response

    def close(self) -> None:
        if self._closed:
            return
        try:
            self._backend.close()
        except Exception as exc:
            raise BackendCloseError("Backend cleanup failed") from exc
        self._closed = True
