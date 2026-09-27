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


async def test_stalled_call_is_abandoned_and_retried(monkeypatch):
    import asyncio

    model = GeminiLanguageModel(api_key="test", model="m", timeout_seconds=30, attempt_timeout_seconds=0.05)
    monkeypatch.setattr(gemini_model, "_RETRY_DELAY_SECONDS", 0)
    outcomes = ["stall", "ok"]

    async def fake_generate(system, prompt):
        if outcomes.pop(0) == "stall":
            await asyncio.sleep(10)
        return "ok"

    monkeypatch.setattr(model, "_generate", fake_generate)
    assert await asyncio.wait_for(model.complete(system="s", prompt="p"), 1) == "ok"


async def test_stream_that_sends_nothing_is_abandoned_and_retried(monkeypatch):
    import asyncio

    model = GeminiLanguageModel(api_key="test", model="m", timeout_seconds=30, first_chunk_timeout_seconds=0.05)
    monkeypatch.setattr(gemini_model, "_RETRY_DELAY_SECONDS", 0)
    attempts = []

    async def fake_stream(system, prompt):
        attempts.append(1)
        if len(attempts) == 1:
            await asyncio.sleep(10)
        yield "Hello"

    monkeypatch.setattr(model, "_generate_stream", fake_stream)
    chunks = await asyncio.wait_for(collect(model), 1)
    assert chunks == ["Hello"]
    assert len(attempts) == 2


async def test_stream_that_stalls_midway_fails_without_repeating_text(monkeypatch):
    import asyncio

    model = GeminiLanguageModel(api_key="test", model="m", timeout_seconds=30, first_chunk_timeout_seconds=0.05)

    async def fake_stream(system, prompt):
        yield "Hel"
        await asyncio.sleep(10)
        yield "lo"

    monkeypatch.setattr(model, "_generate_stream", fake_stream)
    received = []
    with pytest.raises(LanguageModelError, match="stalled"):
        async for chunk in model.stream(system="s", prompt="p"):
            received.append(chunk)
    assert received == ["Hel"]
