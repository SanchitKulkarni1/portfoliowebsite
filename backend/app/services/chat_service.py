"""The /chat use case: question -> Cypher -> guarded read -> grounded answer."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from app.domain.errors import QueryExecutionError, QueryTimeoutError, UnsafeQueryError
from app.domain.models import ChatAnswer, ChatStatus, QueryResult, SafeCypher
from app.domain.ports import GraphRepository, LanguageModel
from app.services import prompts
from app.services.cypher_guard import CypherGuard

logger = logging.getLogger(__name__)

OFF_TOPIC_REPLY = (
    "I can only answer questions about Sanchit's career: his roles, projects, skills and education. "
    "Try asking what he built at Evenflow, or which projects use LangGraph."
)
REFUSED_REPLY = "I can't run that. This assistant only reads Sanchit's career graph."
NO_RESULTS_REPLY = "I couldn't find anything in Sanchit's career graph that matches that question."
FAILED_REPLY = "Sorry, I couldn't work out how to answer that from the graph. Try rephrasing the question."
TIMEOUT_REPLY = "That question took too long to answer from the graph. Try something more specific."


@dataclass(frozen=True)
class ChatSettings:
    max_repair_attempts: int = 1
    max_answer_rows: int = 50
    max_answer_chars: int = 12_000


class ChatService:
    def __init__(
        self,
        llm: LanguageModel,
        repository: GraphRepository,
        guard: CypherGuard,
        settings: ChatSettings = ChatSettings(),
    ) -> None:
        self._llm = llm
        self._repository = repository
        self._guard = guard
        self._settings = settings

    async def ask(self, question: str) -> ChatAnswer:
        started = time.perf_counter()
        answer = await self._answer(question)
        logger.info(
            "chat status=%s latency_ms=%d cypher=%r",
            answer.status.value,
            (time.perf_counter() - started) * 1000,
            answer.cypher,
        )
        return answer

    async def _answer(self, question: str) -> ChatAnswer:
        completion = await self._llm.complete(system=prompts.CYPHER_SYSTEM, prompt=prompts.cypher_prompt(question))
        cypher = prompts.parse_cypher_completion(completion)
        if cypher is None:
            return ChatAnswer(ChatStatus.OFF_TOPIC, OFF_TOPIC_REPLY)

        outcome = await self._query_with_repair(question, cypher)
        if isinstance(outcome, ChatAnswer):
            return outcome
        safe, result = outcome

        if result.is_empty:
            return ChatAnswer(ChatStatus.NO_RESULTS, NO_RESULTS_REPLY, safe.text)

        rows = result.rows[: self._settings.max_answer_rows]
        text = await self._llm.complete(
            system=prompts.ANSWER_SYSTEM,
            prompt=prompts.answer_prompt(question, rows, max_chars=self._settings.max_answer_chars),
        )
        return ChatAnswer(ChatStatus.ANSWERED, text.strip(), safe.text, result.subgraph)

    async def _query_with_repair(self, question: str, cypher: str) -> tuple[SafeCypher, QueryResult] | ChatAnswer:
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
                return safe, await self._repository.run_read(safe)
            except QueryTimeoutError:
                return ChatAnswer(ChatStatus.FAILED, TIMEOUT_REPLY, safe.text)
            except QueryExecutionError as exc:
                logger.info("chat query failed attempt=%d error=%s", attempt, exc)
                if attempt == self._settings.max_repair_attempts:
                    return ChatAnswer(ChatStatus.FAILED, FAILED_REPLY, safe.text)
                completion = await self._llm.complete(
                    system=prompts.CYPHER_SYSTEM,
                    prompt=prompts.repair_prompt(question, safe.text, str(exc)),
                )
                repaired = prompts.parse_cypher_completion(completion)
                if repaired is None:
                    return ChatAnswer(ChatStatus.FAILED, FAILED_REPLY, safe.text)
                cypher = repaired

        raise AssertionError("unreachable")  # the loop always returns
