"""Model-agnostic video description and classification logic."""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any, Protocol

DESCRIPTION_PROMPT = "What is happening in the CCTV footage? Explain in detail."
CLASSIFICATION_PROMPT = """
Is the CCTV footage of the given class? Begin your response with 'Yes' or 'No'.

CCTV footage description: {description}
Class: {class_name}
""".strip()

_BINARY_RESPONSE = re.compile(r"^\s*(yes|no)\b", re.IGNORECASE)


class ContentModel(Protocol):
    """Minimal interface implemented by supported content models."""

    def generate_content(self, contents: Any) -> str:
        """Generate text for model-specific contents."""


class ModelResponseError(RuntimeError):
    """Raised when a model response does not satisfy the data contract."""


def parse_binary_response(text: str) -> bool | None:
    """Parse a leading ``Yes`` or ``No`` token; reject ambiguous prose."""
    match = _BINARY_RESPONSE.match(text)
    if not match:
        return None
    return match.group(1).casefold() == "yes"


def describe(model: ContentModel, video_file: Any) -> str:
    """Generate a detailed description for an uploaded video."""
    text = model.generate_content([video_file, DESCRIPTION_PROMPT])
    if not isinstance(text, str) or not text.strip():
        raise ModelResponseError("The model returned an empty video description.")
    return text.strip()


def classify(
    model: ContentModel,
    description: str,
    classes: Sequence[str],
) -> list[tuple[str, bool | None]]:
    """Classify a description against each class independently."""
    if not description.strip():
        raise ValueError("description cannot be empty")

    results: list[tuple[str, bool | None]] = []
    for class_name in classes:
        if not class_name.strip():
            raise ValueError("class names cannot be empty")
        response = model.generate_content(
            CLASSIFICATION_PROMPT.format(
                description=description,
                class_name=class_name,
            )
        )
        results.append((class_name, parse_binary_response(response)))
    return results


def describe_and_classify(
    model: ContentModel,
    video_file: Any,
    classes: Sequence[str],
) -> tuple[str, list[tuple[str, bool | None]]]:
    """Describe a video and classify the resulting description."""
    description = describe(model, video_file)
    return description, classify(model, description, classes)
