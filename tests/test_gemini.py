from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from cerberus.gemini import (
    FileProcessingError,
    GeminiModel,
    RetryError,
    retry,
    wait_for_file,
)
from cerberus.video_analysis import ModelResponseError


class SequencedFiles:
    def __init__(self, states: list[str]) -> None:
        self._states = iter(states)
        self.names: list[str] = []

    def get(self, *, name: str) -> Any:
        self.names.append(name)
        state = next(self._states)
        return SimpleNamespace(name=name, state=SimpleNamespace(name=state))


def test_retry_uses_bounded_exponential_backoff_then_returns() -> None:
    calls = 0
    delays: list[float] = []

    def operation() -> str:
        nonlocal calls
        calls += 1
        if calls < 4:
            raise OSError("temporary")
        return "ready"

    result = retry(
        operation,
        attempts=4,
        initial_delay=2,
        maximum_delay=3,
        sleep=delays.append,
    )

    assert result == "ready"
    assert calls == 4
    assert delays == [2, 3, 3]


def test_retry_exhaustion_preserves_the_original_cause() -> None:
    calls = 0

    def operation() -> None:
        nonlocal calls
        calls += 1
        raise ConnectionError("offline")

    with pytest.raises(RetryError, match="after 2 attempts") as error:
        retry(operation, attempts=2, initial_delay=0, sleep=lambda _: None)

    assert calls == 2
    assert isinstance(error.value.__cause__, ConnectionError)
    assert str(error.value.__cause__) == "offline"


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"attempts": 0}, "attempts must be at least 1"),
        ({"initial_delay": -1}, "retry delays cannot be negative"),
        ({"maximum_delay": -1}, "retry delays cannot be negative"),
    ],
)
def test_retry_validates_its_budget(kwargs: dict[str, int], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        retry(lambda: None, **kwargs)


def test_wait_for_file_polls_until_active() -> None:
    files = SequencedFiles(["PROCESSING", "ACTIVE"])
    sleeps: list[float] = []
    times = iter([10.0, 10.5, 10.75])

    result = wait_for_file(
        SimpleNamespace(files=files),
        "files/video-1",
        timeout=5,
        poll_interval=0.25,
        sleep=sleeps.append,
        monotonic=lambda: next(times),
    )

    assert result.name == "files/video-1"
    assert result.state.name == "ACTIVE"
    assert files.names == ["files/video-1", "files/video-1"]
    assert sleeps == [0.25]


@pytest.mark.parametrize("state", ["FAILED", "ERROR", "CANCELLED"])
def test_wait_for_file_rejects_terminal_states(state: str) -> None:
    client = SimpleNamespace(files=SequencedFiles([state]))

    with pytest.raises(FileProcessingError, match=state):
        wait_for_file(client, "video", monotonic=lambda: 0)


def test_wait_for_file_times_out_without_sleeping_past_the_deadline() -> None:
    files = SequencedFiles(["PROCESSING"])
    sleeps: list[float] = []
    times = iter([1.0, 4.0])

    with pytest.raises(FileProcessingError, match="Timed out after 2s"):
        wait_for_file(
            SimpleNamespace(files=files),
            "video",
            timeout=2,
            sleep=sleeps.append,
            monotonic=lambda: next(times),
        )

    assert sleeps == []


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"timeout": 0}, "timeout must be positive"),
        ({"poll_interval": 0}, "poll_interval must be positive"),
    ],
)
def test_wait_for_file_validates_polling_arguments(
    kwargs: dict[str, int], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        wait_for_file(SimpleNamespace(), "video", **kwargs)


class Models:
    def __init__(self, response: Any) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []

    def generate_content(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        return self.response


def test_gemini_model_adapts_and_strips_sdk_responses() -> None:
    models = Models(SimpleNamespace(text="  response text  "))
    model = GeminiModel(SimpleNamespace(models=models), "gemini-test")

    assert model.generate_content(["video", "prompt"]) == "response text"
    assert models.calls == [{"model": "gemini-test", "contents": ["video", "prompt"]}]


@pytest.mark.parametrize("text", [None, "", "  "])
def test_gemini_model_rejects_responses_without_text(text: str | None) -> None:
    model = GeminiModel(
        SimpleNamespace(models=Models(SimpleNamespace(text=text))), "gemini-test"
    )

    with pytest.raises(ModelResponseError, match="returned no text"):
        model.generate_content("prompt")
