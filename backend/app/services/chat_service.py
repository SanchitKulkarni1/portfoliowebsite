"""The /chat use case: question -> Cypher -> guarded read -> grounded answer.

Split in two so the answer can be streamed: `prepare()` does everything up to the final
LLM call (cache, Cypher, guard, database); `ask()` or `stream()` then writes the answer."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass, replace

from app.domain.errors import QueryExecutionError, QueryTimeoutError, UnsafeQueryError
from app.domain.models import ChatAnswer, ChatStatus, QueryResult, SafeCypher
from app.domain.ports import GraphRepository, LanguageModel
from app.services import prompts
from app.services.answer_cache import AnswerCache
from app.services.cypher_guard import CypherGuard
from app.services.timing import StageTimings

logger = logging.getLogger(__name__)

OFF_TOPIC_REPLY = (
    "I can only answer questions about Sanchit's career: his roles, projects, skills and education. "
    "Try asking what he built at Evenflow, or which projects use LangGraph."
)
REFUSED_REPLY = "I can't run that. This assistant only reads Sanchit's career graph."
NO_RESULTS_REPLY = "I couldn't find anything in Sanchit's career graph that matches that question."
FAILED_REPLY = "Sorry, I couldn't work out how to answer that from the graph. Try rephrasing the question."
TIMEOUT_REPLY = "That question took too long to answer from the graph. Try something more specific."

# Outcomes that will be the same next time. FAILED ones might succeed on a retry, so they aren't cached.
_CACHEABLE = frozenset({ChatStatus.ANSWERED, ChatStatus.NO_RESULTS, ChatStatus.OFF_TOPIC, ChatStatus.REFUSED})


@dataclass(frozen=True)
class ChatSettings:
    max_repair_attempts: int = 1
    max_answer_rows: int = 50
    max_answer_chars: int = 12_000


@dataclass(frozen=True)
class PreparedAnswer:
    """The result of `prepare()`. When `answer_prompt` is None, `answer` is already final
    (a cache hit, off-topic, no results, refused or failed); otherwise `answer` carries the
    status, Cypher and subgraph, and its text is still to be written from `answer_prompt`."""

    question: str
    answer: ChatAnswer
    answer_prompt: str | None = None
    from_cache: bool = False

    @property
    def is_final(self) -> bool:
        return self.answer_prompt is None


class ChatService:
    def __init__(
        self,
        llm: LanguageModel,
        repository: GraphRepository,
        guard: CypherGuard,
        settings: ChatSettings = ChatSettings(),
        cache: AnswerCache | None = None,
    ) -> None:
        self._llm = llm
        self._repository = repository
        self._guard = guard
        self._settings = settings
        self._cache = cache

    async def ask(self, question: str, timings: StageTimings | None = None, *, pin: bool = False) -> ChatAnswer:
        """Answer in one go. `pin=True` keeps the answer cached for the life of the process."""
        timings = timings if timings is not None else StageTimings()
        prepared = await self.prepare(question, timings)
        answer = prepared.answer
        if not prepared.is_final:
            with timings.measure("llm_answer"):
                text = await self._llm.complete(system=prompts.ANSWER_SYSTEM, prompt=prepared.answer_prompt)
            answer = replace(answer, answer=text.strip())
        self._finish(prepared, answer, timings, pin=pin)
        return answer

    async def stream(self, prepared: PreparedAnswer, timings: StageTimings) -> AsyncIterator[str]:
        """Yield the answer text in chunks. A final answer comes through as a single chunk."""
        if prepared.is_final:
            yield prepared.answer.answer
            self._finish(prepared, prepared.answer, timings)
            return
        parts: list[str] = []
        with timings.measure("llm_answer"):
            async for chunk in self._llm.stream(system=prompts.ANSWER_SYSTEM, prompt=prepared.answer_prompt):
                parts.append(chunk)
                yield chunk
        self._finish(prepared, replace(prepared.answer, answer="".join(parts).strip()), timings)

    async def prepare(self, question: str, timings: StageTimings | None = None) -> PreparedAnswer:
        timings = timings if timings is not None else StageTimings()
        with timings.measure("cache"):
            cached = self._cache.get(question) if self._cache else None
        if cached is not None:
            return PreparedAnswer(question, cached, from_cache=True)

        with timings.measure("llm_cypher"):
            completion = await self._llm.complete(system=prompts.CYPHER_SYSTEM, prompt=prompts.cypher_prompt(question))
        cypher = prompts.parse_cypher_completion(completion)
        if cypher is None:
            return PreparedAnswer(question, ChatAnswer(ChatStatus.OFF_TOPIC, OFF_TOPIC_REPLY))

        outcome = await self._query_with_repair(question, cypher, timings)
        if isinstance(outcome, ChatAnswer):
            return PreparedAnswer(question, outcome)
        safe, result = outcome

        if result.is_empty:
            return PreparedAnswer(question, ChatAnswer(ChatStatus.NO_RESULTS, NO_RESULTS_REPLY, safe.text))

        rows = result.rows[: self._settings.max_answer_rows]
        return PreparedAnswer(
            question,
            ChatAnswer(ChatStatus.ANSWERED, "", safe.text, result.subgraph),
            answer_prompt=prompts.answer_prompt(question, rows, max_chars=self._settings.max_answer_chars),
        )

    def _finish(
        self, prepared: PreparedAnswer, answer: ChatAnswer, timings: StageTimings, *, pin: bool = False
    ) -> None:
        if self._cache and answer.status in _CACHEABLE and (pin or not prepared.from_cache):
            self._cache.put(prepared.question, answer, pinned=pin)
        logger.info(
            "chat status=%s cached=%s total_ms=%.0f %s cypher=%r",
            answer.status.value,
            prepared.from_cache,
            timings.total_ms(),
            timings.as_log(),
            answer.cypher,
        )

    async def _query_with_repair(
        self, question: str, cypher: str, timings: StageTimings
    ) -> tuple[SafeCypher, QueryResult] | ChatAnswer:
        """Guard and run the query. On a database error, ask the model to fix it (bounded retries).

        Guard rejections are never sent back for repair: we don't coach the model past the guard.
        """
        for attempt in range(self._settings.max_repair_attempts + 1):
            try:
                safe = self._guard.validate(cypher)
            except UnsafeQueryError as exc:
                logger.warning("chat refused unsafe cypher=%r reason=%s", cypher, exc)
                return ChatAnswer(ChatStatus.REFUSED, REFUSED_REPLY)

            try:
                with timings.measure("db"):
                    result = await self._repository.run_read(safe)
                return safe, result
            except QueryTimeoutError:
                return ChatAnswer(ChatStatus.FAILED, TIMEOUT_REPLY, safe.text)
            except QueryExecutionError as exc:
                logger.info("chat query failed attempt=%d error=%s", attempt, exc)
                if attempt == self._settings.max_repair_attempts:
                    return ChatAnswer(ChatStatus.FAILED, FAILED_REPLY, safe.text)
                with timings.measure("llm_repair"):
                    completion = await self._llm.complete(
                        system=prompts.CYPHER_SYSTEM,
                        prompt=prompts.repair_prompt(question, safe.text, str(exc)),
                    )
                repaired = prompts.parse_cypher_completion(completion)
                if repaired is None:
                    return ChatAnswer(ChatStatus.FAILED, FAILED_REPLY, safe.text)
                cypher = repaired

        raise AssertionError("unreachable")  # the loop always returns
