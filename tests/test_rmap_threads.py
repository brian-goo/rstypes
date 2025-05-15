import asyncio
from concurrent.futures import ThreadPoolExecutor

import pytest

from rstypes import RMap

rmap_with_factory = RMap(factory=list)
rmap = RMap()


def thread_runner(thread_id: int) -> None:
    async def job() -> None:
        # Test regular set/get
        key = f"key_{thread_id}"
        val = f"value_from_thread_{thread_id}"
        await rmap.set(key, val)
        result = await rmap.get(key)
        print(f"[Thread-{thread_id}] Regular RMap Got: {result}")

        # Test pop
        await rmap.pop(key)
        print(f"[Thread-{thread_id}] Regular RMap After Pop: {await rmap.get(key)}")

        # Test factory default
        factory_key = f"factory_key_{thread_id}"
        # First get will create a new list
        default_list = await rmap_with_factory.get(factory_key)
        print(f"[Thread-{thread_id}] Factory RMap First Get: {default_list}")

        # Modify the list to prove it's the same instance
        await rmap_with_factory.set(factory_key, [1, 2, 3])
        modified = await rmap_with_factory.get(factory_key)
        print(f"[Thread-{thread_id}] Factory RMap After Modify: {modified}")

        # Test pop with factory
        await rmap_with_factory.pop(factory_key)
        print(f"[Thread-{thread_id}] Factory RMap After Pop: {await rmap_with_factory.get(factory_key)}")

        await asyncio.sleep(0.01)  # Simulate some race

    asyncio.run(job())


@pytest.mark.asyncio
async def test_rmap_threads() -> None:
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(thread_runner, i) for i in range(10)]
        for fut in futures:
            fut.result()

    # Verify final state
    for i in range(10):
        key = f"key_{i}"
        assert await rmap.get(key) is None
