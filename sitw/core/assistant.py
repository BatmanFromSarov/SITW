from .backend import (
    BackendCloseError,
    GenerationError,
    InvalidResponseError,
    TestBackend,
    TextBackend,
)


class Assistant:
    def __init__(self, backend: TextBackend | None = None) -> None:
        self._backend = backend if backend is not None else TestBackend()
        self._closed = False

    def respond(self, message: str) -> str:
        if self._closed:
            raise GenerationError("Assistant is closed")
        try:
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
