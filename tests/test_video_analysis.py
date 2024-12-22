from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pytest

from cerberus.video_analysis import (
    CLASSIFICATION_PROMPT,
    DESCRIPTION_PROMPT,
    ModelResponseError,
    classify,
    describe,
    describe_and_classify,
    parse_binary_response,
)


class QueueModel:
    def __init__(self, responses: Iterable[str]) -> None:
        self.responses = iter(responses)
        self.calls: list[Any] = []

    def generate_content(self, contents: Any) -> str:
        self.calls.append(contents)
        return next(self.responses)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Yes", True),
        ("  YES, a courier is visible.", True),
        ("No", False),
        ("\nNo; 'yes' would be incorrect.", False),
        ("The answer is yes.", None),
        ("Possibly", None),
        ("", None),
    ],
)
def test_parse_binary_response_requires_a_leading_token(
    text: str, expected: bool | None
) -> None:
    assert parse_binary_response(text) is expected


def test_describe_strips_text_and_uses_the_video_prompt() -> None:
    video = object()
    model = QueueModel(["  A courier leaves a package.  "])

    assert describe(model, video) == "A courier leaves a package."
    assert model.calls == [[video, DESCRIPTION_PROMPT]]


@pytest.mark.parametrize("response", ["", "   "])
def test_describe_rejects_empty_model_output(response: str) -> None:
    with pytest.raises(ModelResponseError, match="empty video description"):
        describe(QueueModel([response]), object())


def test_classify_preserves_class_order_and_uses_each_class_in_the_prompt() -> None:
    model = QueueModel(["Yes, clearly.", "No, no animal is visible.", "Unclear"])
    classes = ["Package Delivery", "Animal Moving", "Vehicle Moving"]

    result = classify(model, "A courier approaches the porch.", classes)

    assert result == [
        ("Package Delivery", True),
        ("Animal Moving", False),
        ("Vehicle Moving", None),
    ]
    assert model.calls == [
        CLASSIFICATION_PROMPT.format(
            description="A courier approaches the porch.", class_name=class_name
        )
        for class_name in classes
    ]


@pytest.mark.parametrize(
    ("description", "classes", "message"),
    [
        ("", ["Package Delivery"], "description cannot be empty"),
        ("A person walks by.", [""], "class names cannot be empty"),
    ],
)
def test_classify_validates_inputs(
    description: str, classes: list[str], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        classify(QueueModel([]), description, classes)


def test_describe_and_classify_does_not_classify_after_description_failure() -> None:
    model = QueueModel(["  "])

    with pytest.raises(ModelResponseError):
        describe_and_classify(model, object(), ["Package Delivery"])

    assert len(model.calls) == 1


def test_describe_and_classify_runs_the_complete_model_agnostic_flow() -> None:
    model = QueueModel(["A dog crosses the driveway.", "Yes"])

    assert describe_and_classify(model, "video-ref", ["Animal Moving"]) == (
        "A dog crosses the driveway.",
        [("Animal Moving", True)],
    )
