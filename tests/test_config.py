from __future__ import annotations

import pytest

from cerberus.config import (
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_GEMINI_MODEL,
    ConfigurationError,
    GeminiSettings,
    embedding_model_name,
)


def test_gemini_settings_require_an_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_GENERATIVE_AI_API_KEY", raising=False)

    with pytest.raises(ConfigurationError, match="Set GEMINI_API_KEY"):
        GeminiSettings.from_environment()


def test_gemini_settings_support_current_and_legacy_environment_names(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GOOGLE_GENERATIVE_AI_API_KEY", "legacy-key")
    monkeypatch.setenv("GEMINI_API_KEY", "preferred-key")
    monkeypatch.delenv("GEMINI_MODEL", raising=False)

    assert GeminiSettings.from_environment() == GeminiSettings(
        api_key="preferred-key", model=DEFAULT_GEMINI_MODEL
    )


def test_gemini_settings_support_google_sdk_environment_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_GENERATIVE_AI_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", " google-sdk-key ")

    assert GeminiSettings.from_environment().api_key == "google-sdk-key"


def test_gemini_settings_reject_a_whitespace_only_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "   ")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_GENERATIVE_AI_API_KEY", raising=False)

    with pytest.raises(ConfigurationError, match="Set GEMINI_API_KEY"):
        GeminiSettings.from_environment()


def test_gemini_settings_validate_the_model_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "key")
    monkeypatch.setenv("GEMINI_MODEL", "   ")

    with pytest.raises(ConfigurationError, match="GEMINI_MODEL cannot be empty"):
        GeminiSettings.from_environment()


def test_embedding_model_uses_a_default_and_rejects_blank_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("EMBEDDING_MODEL", raising=False)
    assert embedding_model_name() == DEFAULT_EMBEDDING_MODEL

    monkeypatch.setenv("EMBEDDING_MODEL", "   ")
    with pytest.raises(ConfigurationError, match="EMBEDDING_MODEL cannot be empty"):
        embedding_model_name()
