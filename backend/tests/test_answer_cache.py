from app.domain.models import ChatAnswer, ChatStatus
from app.services.answer_cache import AnswerCache

ANSWER = ChatAnswer(ChatStatus.ANSWERED, "Sanchit built gitEQ.")


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def test_hit_ignores_case_spacing_and_trailing_punctuation():
    cache = AnswerCache(max_entries=10, ttl_seconds=60)
    cache.put("Tell me about gitEQ?", ANSWER)
    assert cache.get("  tell me   about GITEQ ") is ANSWER
    assert cache.get("Tell me about DodgeAI") is None


def test_entries_expire():
    clock = Clock()
    cache = AnswerCache(max_entries=10, ttl_seconds=60, clock=clock)
    cache.put("q", ANSWER)
    clock.now = 59
    assert cache.get("q") is ANSWER
    clock.now = 60
    assert cache.get("q") is None


def test_least_recently_used_entry_is_evicted():
    cache = AnswerCache(max_entries=2, ttl_seconds=60)
    cache.put("a", ANSWER)
    cache.put("b", ANSWER)
    cache.get("a")  # b is now least recently used
    cache.put("c", ANSWER)
    assert cache.get("a") and cache.get("c")
    assert cache.get("b") is None


def test_zero_ttl_disables_caching():
    cache = AnswerCache(max_entries=10, ttl_seconds=0)
    cache.put("q", ANSWER)
    assert cache.get("q") is None
