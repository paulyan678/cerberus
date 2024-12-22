"""Small, dependency-free JSON and JSONL helpers."""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any, Protocol, TextIO

JsonObject = dict[str, Any]


class TextResource(Protocol):
    """Path-like resource supporting text reads (including package resources)."""

    def open(self, mode: str = "r", *, encoding: str | None = None) -> TextIO: ...


class DataFormatError(ValueError):
    """Raised when a JSONL record is malformed."""


def read_jsonl(stream: TextIO) -> Iterator[JsonObject]:
    """Yield JSON objects from *stream*, including useful line diagnostics."""
    for line_number, raw_line in enumerate(stream, start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            raise DataFormatError(
                f"Invalid JSON on line {line_number}: {error.msg}"
            ) from error
        if not isinstance(value, dict):
            raise DataFormatError(
                f"Expected a JSON object on line {line_number}, "
                f"got {type(value).__name__}."
            )
        yield value


def write_jsonl(records: Iterable[object], stream: TextIO) -> None:
    """Write records as one compact JSON value per line."""
    for record in records:
        json.dump(record, stream, ensure_ascii=False, separators=(",", ":"))
        stream.write("\n")


def _open_text(path: str | Path | TextResource) -> TextIO:
    if isinstance(path, (str, Path)):
        return Path(path).open(encoding="utf-8")
    return path.open("r", encoding="utf-8")


def load_jsonl(path: str | Path | TextResource) -> list[JsonObject]:
    """Load a JSONL file into memory."""
    with _open_text(path) as stream:
        return list(read_jsonl(stream))


def load_json(path: str | Path | TextResource) -> Any:
    """Load a UTF-8 JSON file."""
    with _open_text(path) as stream:
        return json.load(stream)
