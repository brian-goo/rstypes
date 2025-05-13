import asyncio
from typing import NamedTuple

import pytest

from rstypes import RCacheMap


class Foo(NamedTuple):
    name: str
    age: int


@pytest.mark.asyncio
async def test_basic_cache_behavior() -> None:
    cache = RCacheMap()

    await cache.pop("hello")
    assert await cache.get("hello") is None

    await cache.set(key="hello", value=123, ttl=1.0)  # 1 second TTL
    await cache.set(key="cool_lock", value=asyncio.Lock(), ttl=2.0)  # 2 seconds TTL
    await cache.set(key="user", value=Foo(name="Alice", age=30), ttl=2.0)  # 2 seconds TTL

    assert await cache.get("hello") == 123
    assert isinstance(await cache.get("cool_lock"), asyncio.Lock)
    user = await cache.get("user")
    assert isinstance(user, Foo)
    assert user.name == "Alice"
    assert user.age == 30

    # Wait for first value to expire
    await asyncio.sleep(1.1)
    assert await cache.get("hello") is None
    assert isinstance(await cache.get("cool_lock"), asyncio.Lock)

    await cache.pop("cool_lock")
    assert await cache.get("cool_lock") is None

    # Test pop_expired
    await cache.set(key="hello", value=123, ttl=1.0)
    await cache.set(key="cool_lock", value=asyncio.Lock(), ttl=1.0)
    await cache.set(key="user", value=Foo(name="Alice", age=30), ttl=1.0)
    await asyncio.sleep(1.1)
    await cache.pop_expired()
    assert await cache.get("hello") is None
    assert await cache.get("cool_lock") is None
    assert await cache.get("user") is None


@pytest.mark.asyncio
async def test_concurrent_set_and_get() -> None:
    cache = RCacheMap()

    await asyncio.gather(
        cache.set(key="a", value=1, ttl=1.0),
        cache.set(key="b", value=asyncio.Lock(), ttl=2.0),
        cache.set(key="c", value=asyncio.get_running_loop().create_future(), ttl=3.0),
    )

    results = await asyncio.gather(
        cache.get("a"),
        cache.get("b"),
        cache.get("c"),
    )
    assert results[0] == 1
    assert isinstance(results[1], asyncio.Lock)
    assert isinstance(results[2], asyncio.Future)


@pytest.mark.asyncio
async def test_concurrent_get_set_race() -> None:
    cache = RCacheMap()

    async def set_key():
        await cache.set(key="x", value=42, ttl=1.0)

    async def get_key():
        val = await cache.get("x")
        assert val in (None, 42)  # Value could be None or 42 due to race

    await asyncio.gather(set_key(), get_key(), set_key(), get_key())


@pytest.mark.asyncio
async def test_expiry_behavior() -> None:
    cache = RCacheMap()
    await cache.set(key="a", value=1, ttl=1.0)
    await cache.set(key="b", value=2, ttl=1.0)
    await cache.set(key="c", value=3, ttl=1.0)
    await asyncio.sleep(1.1)
    await cache.pop_expired()
    assert await cache.get("a") is None
    assert await cache.get("b") is None
    assert await cache.get("c") is None


@pytest.mark.asyncio
async def test_int_key_basic_behavior() -> None:
    cache = RCacheMap()

    await cache.pop(42)
    assert await cache.get(42) is None

    await cache.set(key=42, value="answer", ttl=1.0)
    await cache.set(key=0, value="zero", ttl=1.0)
    await cache.set(key=-1, value="negative", ttl=1.0)

    assert await cache.get(42) == "answer"
    assert await cache.get(0) == "zero"
    assert await cache.get(-1) == "negative"

    await cache.pop(42)
    assert await cache.get(42) is None

    # Expiry
    await cache.set(key=99, value="expire", ttl=0.5)
    await asyncio.sleep(0.6)
    await cache.pop_expired()
    assert await cache.get(99) is None


@pytest.mark.asyncio
async def test_int_key_concurrent() -> None:
    cache = RCacheMap()

    await asyncio.gather(
        cache.set(key=1, value="one", ttl=1.0),
        cache.set(key=2, value=asyncio.Lock(), ttl=2.0),
        cache.set(key=3, value=asyncio.get_running_loop().create_future(), ttl=3.0),
    )

    results = await asyncio.gather(
        cache.get(1),
        cache.get(2),
        cache.get(3),
    )
    assert results[0] == "one"
    assert isinstance(results[1], asyncio.Lock)
    assert isinstance(results[2], asyncio.Future)


@pytest.mark.asyncio
async def test_int_key_get_set_race() -> None:
    cache = RCacheMap()

    async def set_key():
        await cache.set(key=100, value=42, ttl=1.0)

    async def get_key():
        val = await cache.get(100)
        assert val in (None, 42)  # Value could be None or 42 due to race

    await asyncio.gather(set_key(), get_key(), set_key(), get_key())
