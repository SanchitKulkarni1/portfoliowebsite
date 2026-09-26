"""Google Gemini adapter for the LanguageModel port."""

from __future__ import annotations

import asyncio
import logging

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from app.domain.errors import LanguageModelBusyError, LanguageModelError

logger = logging.getLogger(__name__)

# Quota exhausted (429) or model overloaded (503): transient, worth retrying later.
_BUSY_STATUS_CODES = frozenset({429, 503})
# Server-side hiccups (5xx other than overload) and transport errors get one quick retry.
_RETRY_DELAY_SECONDS = 0.8


class GeminiLanguageModel:
    def __init__(self, *, api_key: str, model: str, timeout_seconds: float, temperature: float = 0.0) -> None:
        self._client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=int(timeout_seconds * 1000)),
        )
        self._model = model
        self._temperature = temperature

    async def complete(self, *, system: str, prompt: str) -> str:
        try:
            return await self._generate(system, prompt)
        except LanguageModelBusyError:
            raise
        except LanguageModelError as first:
            logger.warning("Gemini call failed, retrying once: %s", first)
            await asyncio.sleep(_RETRY_DELAY_SECONDS)
            return await self._generate(system, prompt)

    async def _generate(self, system: str, prompt: str) -> str:
        try:
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system,
                    temperature=self._temperature,
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                ),
            )
        except genai_errors.APIError as exc:
            if exc.code in _BUSY_STATUS_CODES:
                raise LanguageModelBusyError(f"Gemini is busy ({exc.code}): {exc.message}") from exc
            raise LanguageModelError(f"Gemini request failed: {exc}") from exc
        except Exception as exc:  # transport errors, timeouts
            raise LanguageModelError(f"Gemini request failed: {exc}") from exc
        text = response.text
        if not text or not text.strip():
            raise LanguageModelError("Gemini returned an empty response.")
        return text

    async def aclose(self) -> None:
        await self._client.aio.aclose()
