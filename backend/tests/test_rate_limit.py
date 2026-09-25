from app.api.rate_limit import SlidingWindowRateLimiter


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def test_allows_up_to_the_limit_then_blocks_with_retry_after():
    clock = Clock()
    limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=60, clock=clock)

    assert limiter.hit("a").allowed
    clock.now += 10
    assert limiter.hit("a").allowed
    blocked = limiter.hit("a")
    assert not blocked.allowed
    assert blocked.retry_after_seconds == 50


def test_window_slides():
    clock = Clock()
    limiter = SlidingWindowRateLimiter(max_requests=1, window_seconds=60, clock=clock)
    assert limiter.hit("a").allowed
    clock.now += 60
    assert limiter.hit("a").allowed


def test_clients_are_independent():
    limiter = SlidingWindowRateLimiter(max_requests=1, window_seconds=60, clock=Clock())
    assert limiter.hit("a").allowed
    assert limiter.hit("b").allowed
    assert not limiter.hit("a").allowed


def test_idle_clients_are_evicted_when_over_capacity():
    clock = Clock()
    limiter = SlidingWindowRateLimiter(max_requests=1, window_seconds=60, max_tracked_clients=2, clock=clock)
    limiter.hit("a")
    limiter.hit("b")
    clock.now += 61
    limiter.hit("c")
    assert set(limiter._hits) == {"c"}
