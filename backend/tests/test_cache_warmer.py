from app.domain.errors import LanguageModelBusyError
from app.domain.models import ChatStatus
from app.services.answer_cache import AnswerCache
from app.services.cache_warmer import warm_answers
from app.services.chat_service import ChatService
from app.services.cypher_guard import CypherGuard
from tests.fakes import FakeGraphRepository, FakeLanguageModel
from tests.test_chat_service import QUERY, RESULT


def service(llm, repo, cache):
    return ChatService(llm, repo, CypherGuard(max_rows=50), cache=cache)


async def test_warm_up_pins_answers_and_survives_a_busy_llm():
    cache = AnswerCache(max_entries=10, ttl_seconds=0)  # TTL cache off: only pinned answers stick
    llm = FakeLanguageModel([QUERY, "gitEQ is a repo analyser.", LanguageModelBusyError("429"), "NO_QUERY"])
    chat = service(llm, FakeGraphRepository([RESULT]), cache)

    answered = await warm_answers(
        chat,
        ["Tell me about gitEQ", "Which projects use LangGraph?", "What's the weather?"],
        spacing_seconds=0,
        busy_backoff_seconds=0,
    )

    assert answered == 1
    assert cache.get("tell me about giteq").answer == "gitEQ is a repo analyser."
    assert cache.get("Which projects use LangGraph?") is None  # skipped while the LLM was busy
    assert cache.get("What's the weather?").status is ChatStatus.OFF_TOPIC  # still pinned: stable outcome


async def test_pinned_answer_is_served_without_llm_calls():
    cache = AnswerCache(max_entries=10, ttl_seconds=60)
    llm = FakeLanguageModel([QUERY, "gitEQ is a repo analyser."])
    chat = service(llm, FakeGraphRepository([RESULT]), cache)
    await warm_answers(chat, ["Tell me about gitEQ"], spacing_seconds=0)

    again = await chat.ask("Tell me about gitEQ")

    assert again.answer == "gitEQ is a repo analyser."
    assert len(llm.calls) == 2  # only the warm-up's
