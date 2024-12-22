"""Cerberus CCTV analysis and retrieval toolkit."""

from cerberus.video_analysis import (
    CLASSIFICATION_PROMPT,
    DESCRIPTION_PROMPT,
    classify,
    describe,
    describe_and_classify,
    parse_binary_response,
)

__all__ = [
    "CLASSIFICATION_PROMPT",
    "DESCRIPTION_PROMPT",
    "classify",
    "describe",
    "describe_and_classify",
    "parse_binary_response",
]
__version__ = "0.1.0"
