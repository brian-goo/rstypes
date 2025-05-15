import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import NamedTuple

import pytest

from rstypes import RCacheMap


class Foo(NamedTuple):
    name: str
    age: int


cache = RCacheMap()


def thread_runner(thread_id: int) -> None:
    async def job() -> None:
        # Test regular set/get with string keys
        key = f"key_{thread_id}"
        val = f"value_from_thread_{thread_id}"
        await cache.set(key=key, value=val, ttl=1.0)
        result = await cache.get(key)
        print(f"[Thread-{thread_id}] Regular Cache Got: {result}")

        # Test pop
        await cache.pop(key)
        print(f"[Thread-{thread_id}] Regular Cache After Pop: {await cache.get(key)}")

        # Test with complex objects
        user_key = f"user_{thread_id}"
        user = Foo(name=f"User_{thread_id}", age=20 + thread_id)
        await cache.set(key=user_key, value=user, ttl=1.0)
        cached_user = await cache.get(user_key)
        print(f"[Thread-{thread_id}] Cache User Object: {cached_user}")

        # Test with asyncio objects
        lock_key = f"lock_{thread_id}"
        lock = asyncio.Lock()
        await cache.set(key=lock_key, value=lock, ttl=1.0)
        cached_lock = await cache.get(lock_key)
        print(f"[Thread-{thread_id}] Cache Lock Object: {cached_lock}")

        # Test expiry
        expire_key = f"expire_{thread_id}"
        await cache.set(key=expire_key, value="will_expire", ttl=0.5)
        await asyncio.sleep(0.6)
        print(f"[Thread-{thread_id}] Expired Value: {await cache.get(expire_key)}")

        await asyncio.sleep(0.01)  # Simulate some race

    asyncio.run(job())


@pytest.mark.asyncio
async def test_rcachemap_threads() -> None:
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(thread_runner, i) for i in range(10)]
        for fut in futures:
            fut.result()

    # Verify final state
    for i in range(10):
        key = f"key_{i}"
        assert await cache.get(key) is None

        expire_key = f"expire_{i}"
        assert await cache.get(expire_key) is None
