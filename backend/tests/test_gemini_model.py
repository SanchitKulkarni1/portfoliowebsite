"""The Gemini adapter's retry policy, with the SDK call replaced by a scripted fake."""

import pytest

from app.domain.errors import LanguageModelBusyError, LanguageModelError
from app.infrastructure import gemini_model
from app.infrastructure.gemini_model import GeminiLanguageModel


@pytest.fixture
def model(monkeypatch):
    monkeypatch.setattr(gemini_model, "_RETRY_DELAY_SECONDS", 0)
    return GeminiLanguageModel(api_key="test", model="test-model", timeout_seconds=5)


def script(monkeypatch, model, outcomes):
    calls = []

    async def fake_generate(system, prompt):
        calls.append(prompt)
        outcome = outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(model, "_generate", fake_generate)
    return calls


async def test_transient_error_is_retried_once(monkeypatch, model):
    calls = script(monkeypatch, model, [LanguageModelError("500 INTERNAL"), "ok"])
    assert await model.complete(system="s", prompt="p") == "ok"
    assert len(calls) == 2


async def test_second_failure_propagates(monkeypatch, model):
    calls = script(monkeypatch, model, [LanguageModelError("500"), LanguageModelError("500 again")])
    with pytest.raises(LanguageModelError, match="again"):
        await model.complete(system="s", prompt="p")
    assert len(calls) == 2


async def test_quota_errors_are_not_retried(monkeypatch, model):
    calls = script(monkeypatch, model, [LanguageModelBusyError("429")])
    with pytest.raises(LanguageModelBusyError):
        await model.complete(system="s", prompt="p")
    assert len(calls) == 1
