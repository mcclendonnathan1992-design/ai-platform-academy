from gateway.cache import LRUCache, make_key
from gateway.ratelimit import RateLimiter


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def test_rate_limiter_blocks_after_limit_then_recovers():
    clock = FakeClock()
    limiter = RateLimiter(2, window_s=60, clock=clock)
    assert limiter.allow("a") == (True, 0.0)
    assert limiter.allow("a") == (True, 0.0)
    allowed, retry = limiter.allow("a")
    assert allowed is False
    assert 0 < retry <= 60
    clock.now += 61
    assert limiter.allow("a")[0] is True


def test_rate_limiter_is_per_client():
    limiter = RateLimiter(1, clock=FakeClock())
    assert limiter.allow("a")[0] is True
    assert limiter.allow("b")[0] is True
    assert limiter.allow("a")[0] is False


def test_rate_limiter_zero_disables():
    limiter = RateLimiter(0, clock=FakeClock())
    assert all(limiter.allow("a")[0] for _ in range(100))


def test_cache_returns_stored_value():
    cache = LRUCache(2)
    cache.store("k", "v")
    assert cache.lookup("k") == "v"
    assert cache.lookup("missing") is None


def test_cache_evicts_least_recently_used():
    cache = LRUCache(2)
    cache.store("a", "1")
    cache.store("b", "2")
    cache.lookup("a")  # a is now most recent
    cache.store("c", "3")  # evicts b
    assert cache.lookup("b") is None
    assert cache.lookup("a") == "1"
    assert cache.lookup("c") == "3"


def test_cache_size_zero_disables():
    cache = LRUCache(0)
    cache.store("a", "1")
    assert cache.lookup("a") is None
    assert len(cache) == 0


def test_cache_key_depends_on_model_prompt_and_tokens():
    base = make_key("m", "p", 10)
    assert base == make_key("m", "p", 10)
    assert base != make_key("m2", "p", 10)
    assert base != make_key("m", "p2", 10)
    assert base != make_key("m", "p", 11)
