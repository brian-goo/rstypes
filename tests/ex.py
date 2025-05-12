import asyncio
from typing import NamedTuple, cast

from rstypes import RMap


class Foo(NamedTuple):
    name: str
    age: int


async def example() -> None:
    d = RMap()

    await d.pop("hello")
    print("No panic: `None` if key not in map:", await d.get("hello"))

    await d.set(key="hello", value=123)
    await d.set(key="cool_lock", value=asyncio.Lock())
    await d.set(key="user", value=Foo(name="Alice", age=30))

    print(await d.get("hello"))
    print(await d.get("cool_lock"))
    print(await d.get("user"))

    await d.pop("hello")
    print(await d.get("hello"))  # None


async def default_dict() -> None:
    d = RMap(asyncio.Lock)
    print(await d.get("foo"))
    await d.set("foo", 7)
    print(await d.get("foo"))

    d = RMap(lambda: Foo(name="Alice", age=30))
    print(await d.get("foo"))


async def default_dict_with_ctx() -> None:
    d = RMap(asyncio.Lock)
    async with cast(asyncio.Lock, await d.get("foo")):
        print("foo acquired lock")


async def concurrent_set(d: RMap) -> None:
    await asyncio.gather(
        d.set("a", 1),
        d.set("b", asyncio.Lock()),
        d.set("c", asyncio.get_running_loop().create_future()),
    )


async def concurrent_get(d: RMap) -> None:
    results = await asyncio.gather(
        d.get("a"),
        d.get("b"),
        d.get("c"),
    )
    print("Concurrent get results:", results)


async def concurrent_get_set(d: RMap) -> None:
    """
    Mixes set and get on the same key, potentially racing them (great test of mutex safety!)
    """

    async def set_key():
        await d.set("x", 42)

    async def get_key():
        val = await d.get("x")
        print("Get x:", val)

    await asyncio.gather(set_key(), get_key(), set_key(), get_key())


async def main() -> None:
    print("=== Example ===")
    await example()

    print()
    print("=== Default Dict ===")
    await default_dict()

    print()
    print("=== Default Dict with Ctx ===")
    await default_dict_with_ctx()

    d = RMap()
    print()
    print("=== Concurrent Set ===")
    await concurrent_set(d)

    print("=== Concurrent Get ===")
    await concurrent_get(d)

    print("=== Concurrent Get/Set ===")
    await concurrent_get_set(d)


asyncio.run(main())
