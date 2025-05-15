import asyncio
import random
from typing import cast

import pytest

from rstypes import RCacheMap, RMap


async def writer_task_rmap(shared_dict: RMap, task_id: int) -> None:
    key = f"key_{task_id}"
    value = f"val_from_task_{task_id}"

    await asyncio.sleep(random.uniform(0.01, 0.1))
    await shared_dict.set(key=key, value=value)

    # Test pop after setting
    await shared_dict.pop(key)


async def reader_task_rmap(shared_dict: RMap, task_id: int) -> None:
    key = f"lock_key_{task_id}"
    await asyncio.sleep(random.uniform(0.01, 0.1))

    lock = await shared_dict.get(key)
    assert isinstance(lock, asyncio.Lock)

    async with cast(asyncio.Lock, lock):
        await asyncio.sleep(0.01)


async def writer_task_rcache(shared_dict: RCacheMap, task_id: int) -> None:
    key = f"key_{task_id}"
    value = f"val_from_task_{task_id}"

    await asyncio.sleep(random.uniform(0.01, 0.1))
    await shared_dict.set(key=key, value=value, ttl=1.0)

    # Test pop after setting
    await shared_dict.pop(key)


async def reader_task_rcache(shared_dict: RCacheMap, task_id: int) -> None:
    key = f"lock_key_{task_id}"
    await asyncio.sleep(random.uniform(0.01, 0.1))

    lock = await shared_dict.get(key)
    if lock is not None:
        assert isinstance(lock, asyncio.Lock)
        async with cast(asyncio.Lock, lock):
            await asyncio.sleep(0.01)


@pytest.mark.asyncio
async def test_rmap_contention() -> None:
    shared_dict = RMap(factory=asyncio.Lock)
    tasks = []

    # Spawn multiple writers
    for i in range(50):
        tasks.append(writer_task_rmap(shared_dict, i))

    # Spawn multiple readers that will use the factory-created locks
    for i in range(50):
        tasks.append(reader_task_rmap(shared_dict, i))

    await asyncio.gather(*tasks)


@pytest.mark.asyncio
async def test_rcache_contention() -> None:
    shared_dict = RCacheMap()
    tasks = []

    # Spawn multiple writers
    for i in range(50):
        tasks.append(writer_task_rcache(shared_dict, i))

    # Spawn multiple readers that will use the factory-created locks
    for i in range(50):
        tasks.append(reader_task_rcache(shared_dict, i))

    await asyncio.gather(*tasks)
