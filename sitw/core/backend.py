"""Text generation boundary; no model or inference dependencies."""

from typing import Protocol, runtime_checkable


class GenerationError(Exception):
    """The backend could not generate a response."""


class InvalidResponseError(GenerationError):
    """Generation returned something other than nonblank text."""


class BackendCloseError(Exception):
    """The backend could not release its resources."""


class TextBackend(Protocol):
    """Assistant owns the backend and calls close on shutdown.

    generate returns nonblank text or raises an exception. close releases
    resources and must tolerate repeated calls. Constructors must clean up
    their own resources if initialization fails.
    """

    def generate(self, message: str) -> str: ...

    def close(self) -> None: ...


@runtime_checkable
class ChatBackend(TextBackend, Protocol):
    """Optional dialogue support; messages include the current user entry."""

    def generate_chat(self, messages: list[dict[str, str]]) -> str: ...


class TestBackend:
    """Deterministic placeholder preserving the original CLI response."""

    def generate(self, message: str) -> str:
        return f"SITW получил сообщение: {message}"

    def close(self) -> None:
        pass
