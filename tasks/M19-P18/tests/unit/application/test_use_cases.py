"""
Test application layer
"""

from types import SimpleNamespace

from pytest import MonkeyPatch

from app.application import use_cases


def test_reply(monkeypatch: MonkeyPatch) -> None:
    """Ensures that the reply method works correctly."""

    expected = "Expected output"
    monkeypatch.setattr(use_cases.llm_service, "reply", lambda m: expected)

    response = use_cases.reply(expected)

    assert response == expected


def test_llm_reply(monkeypatch: MonkeyPatch) -> None:
    """Ensures LLMService.reply returns the content of the LLM response."""

    expected = "Expected output"
    fake_response = SimpleNamespace(content='Expected output')
    fake_llm = SimpleNamespace(invoke=lambda messages: fake_response)
    monkeypatch.setattr(use_cases.llm_service, "llm", fake_llm)

    response = use_cases.llm_service.reply('Hello')

    assert response == expected
