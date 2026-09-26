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


def script_stream(monkeypatch, model, attempts):
    """Each attempt is a list of chunks, optionally ending in an exception raised after them."""
    calls = []

    async def fake_stream(system, prompt):
        calls.append(prompt)
        for item in attempts.pop(0):
            if isinstance(item, Exception):
                raise item
            yield item

    monkeypatch.setattr(model, "_generate_stream", fake_stream)
    return calls


async def collect(model):
    return [chunk async for chunk in model.stream(system="s", prompt="p")]


async def test_stream_retries_a_failure_before_any_text(monkeypatch, model):
    calls = script_stream(monkeypatch, model, [[LanguageModelError("500")], ["Hel", "lo"]])
    assert await collect(model) == ["Hel", "lo"]
    assert len(calls) == 2


async def test_stream_does_not_retry_after_text_was_sent(monkeypatch, model):
    calls = script_stream(monkeypatch, model, [["Hel", LanguageModelError("500")], ["never"]])
    chunks = []
    with pytest.raises(LanguageModelError):
        async for chunk in model.stream(system="s", prompt="p"):
            chunks.append(chunk)
    assert chunks == ["Hel"]
    assert len(calls) == 1


async def test_empty_stream_is_an_error(monkeypatch, model):
    script_stream(monkeypatch, model, [[], []])
    with pytest.raises(LanguageModelError, match="empty"):
        await collect(model)
