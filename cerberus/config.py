"""Validated application settings."""

from __future__ import annotations

from dataclasses import dataclass
from os import getenv

DEFAULT_GEMINI_MODEL = "gemini-3.5-flash"
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/multi-qa-mpnet-base-cos-v1"


class ConfigurationError(ValueError):
    """Raised when required runtime configuration is absent or invalid."""


@dataclass(frozen=True)
class GeminiSettings:
    """Configuration required by the Gemini-backed video pipeline."""

    api_key: str
    model: str = DEFAULT_GEMINI_MODEL

    @classmethod
    def from_environment(cls) -> GeminiSettings:
        """Load Gemini settings and fail with an actionable error."""
        api_key = (
            getenv("GEMINI_API_KEY")
            or getenv("GOOGLE_API_KEY")
            or getenv("GOOGLE_GENERATIVE_AI_API_KEY")
        )
        api_key = api_key.strip() if api_key else ""
        if not api_key:
            raise ConfigurationError(
                "Set GEMINI_API_KEY in the environment or a .env file."
            )

        model = getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip()
        if not model:
            raise ConfigurationError("GEMINI_MODEL cannot be empty.")

        return cls(api_key=api_key, model=model)


def embedding_model_name() -> str:
    """Return the configured sentence-transformer model name."""
    value = getenv("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL).strip()
    if not value:
        raise ConfigurationError("EMBEDDING_MODEL cannot be empty.")
    return value
