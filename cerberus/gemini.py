"""Google Gen AI SDK adapter and finite file-processing helpers."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any, TypeVar

from cerberus.config import GeminiSettings
from cerberus.video_analysis import ModelResponseError

T = TypeVar("T")


class RetryError(RuntimeError):
    """Raised after an operation exhausts its retry budget."""


class FileProcessingError(RuntimeError):
    """Raised when Gemini cannot make an uploaded file ready in time."""


def retry(
    operation: Callable[[], T],
    *,
    attempts: int = 3,
    initial_delay: float = 1.0,
    maximum_delay: float = 8.0,
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """Run an operation with bounded exponential backoff.

    The helper deliberately has a finite default. Callers should still avoid
    retrying known permanent validation or authentication failures.
    """
    if attempts < 1:
        raise ValueError("attempts must be at least 1")
    if initial_delay < 0 or maximum_delay < 0:
        raise ValueError("retry delays cannot be negative")

    delay = initial_delay
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except Exception as error:  # Boundary around an external SDK call.
            last_error = error
            if attempt == attempts:
                break
            sleep(min(delay, maximum_delay))
            delay = min(delay * 2, maximum_delay)

    raise RetryError(f"Operation failed after {attempts} attempts") from last_error


def _state_name(file: Any) -> str:
    state = getattr(file, "state", None)
    value = getattr(state, "name", state)
    return str(value or "").upper()


def wait_for_file(
    client: Any,
    name: str,
    *,
    timeout: float = 300.0,
    poll_interval: float = 2.0,
    sleep: Callable[[float], None] = time.sleep,
    monotonic: Callable[[], float] = time.monotonic,
) -> Any:
    """Poll an uploaded Gemini file until it is active, failed, or timed out."""
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    if poll_interval <= 0:
        raise ValueError("poll_interval must be positive")

    deadline = monotonic() + timeout
    first_request = True
    while True:
        if not first_request and monotonic() >= deadline:
            raise FileProcessingError(
                f"Timed out after {timeout:g}s waiting for Gemini file {name!r}."
            )
        first_request = False
        file = client.files.get(name=name)
        state = _state_name(file)
        if state == "ACTIVE":
            return file
        if state in {"FAILED", "ERROR", "CANCELLED"}:
            raise FileProcessingError(
                f"Gemini file {name!r} entered terminal state {state}."
            )
        remaining = deadline - monotonic()
        if remaining <= 0:
            raise FileProcessingError(
                f"Timed out after {timeout:g}s waiting for Gemini file {name!r}."
            )
        sleep(min(poll_interval, remaining))


class GeminiModel:
    """Adapt ``google.genai.Client`` to the project content-model protocol."""

    def __init__(self, client: Any, model_name: str) -> None:
        self._client = client
        self._model_name = model_name

    def generate_content(self, contents: Any) -> str:
        """Generate content and require a non-empty text response."""
        response = self._client.models.generate_content(
            model=self._model_name,
            contents=contents,
        )
        text = getattr(response, "text", None)
        if not isinstance(text, str) or not text.strip():
            raise ModelResponseError(
                "Gemini returned no text; inspect safety settings and finish reason."
            )
        return text.strip()


def create_client(settings: GeminiSettings) -> Any:
    """Create a Google Gen AI client without importing the SDK at module load."""
    from google import genai

    return genai.Client(api_key=settings.api_key)
