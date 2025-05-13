import asyncio
from typing import NamedTuple, cast

import pytest

from rstypes import RMap


class Foo(NamedTuple):
    name: str
    age: int


@pytest.mark.asyncio
async def test_basic_operations() -> None:
    d = RMap()

    await d.pop("hello")
    assert (await d.get("hello")) is None

    await d.set(key="hello", value=123)
    await d.set(key="cool_lock", value=asyncio.Lock())
    await d.set(key="user", value=Foo(name="Alice", age=30))

    assert (await d.get("hello")) == 123
    assert isinstance(await d.get("cool_lock"), asyncio.Lock)
    user = await d.get("user")
    assert isinstance(user, Foo)
    assert user.name == "Alice"
    assert user.age == 30

    await d.pop("hello")
    assert (await d.get("hello")) is None


@pytest.mark.asyncio
async def test_default_dict() -> None:
    d = RMap(asyncio.Lock)
    lock = await d.get("foo")
    assert isinstance(lock, asyncio.Lock)

    await d.set("foo", 7)
    assert (await d.get("foo")) == 7

    d = RMap(lambda: Foo(name="Alice", age=30))
    user = await d.get("foo")
    assert isinstance(user, Foo)
    assert user.name == "Alice"
    assert user.age == 30


@pytest.mark.asyncio
async def test_default_dict_with_context() -> None:
    d = RMap(asyncio.Lock)
    async with cast(asyncio.Lock, await d.get("foo")):
        pass  # Lock should be acquired and released


@pytest.mark.asyncio
async def test_concurrent_operations() -> None:
    d = RMap()

    # Test concurrent set
    await asyncio.gather(
        d.set("a", 1),
        d.set("b", asyncio.Lock()),
        d.set("c", asyncio.get_running_loop().create_future()),
    )

    # Test concurrent get
    results = await asyncio.gather(
        d.get("a"),
        d.get("b"),
        d.get("c"),
    )
    assert results[0] == 1
    assert isinstance(results[1], asyncio.Lock)
    assert isinstance(results[2], asyncio.Future)


@pytest.mark.asyncio
async def test_concurrent_get_set() -> None:
    d = RMap()

    async def set_key():
        await d.set("x", 42)

    async def get_key():
        val = await d.get("x")
        assert val in (None, 42)  # Value could be None or 42

    await asyncio.gather(set_key(), get_key(), set_key(), get_key())


@pytest.mark.asyncio
async def test_int_keys() -> None:
    d = RMap()

    # Test basic operations with int keys
    await d.pop(42)
    assert await d.get(42) is None

    await d.set(key=42, value="answer")
    await d.set(key=0, value="zero")
    await d.set(key=-1, value="negative")

    assert await d.get(42) == "answer"
    assert await d.get(0) == "zero"
    assert await d.get(-1) == "negative"

    await d.pop(42)
    assert await d.get(42) is None


@pytest.mark.asyncio
async def test_int_keys_with_default() -> None:
    d = RMap(asyncio.Lock)
    lock = await d.get(42)
    assert isinstance(lock, asyncio.Lock)

    await d.set(key=42, value=7)
    assert await d.get(42) == 7

    d = RMap(lambda: Foo(name="Alice", age=30))
    user = await d.get(42)
    assert isinstance(user, Foo)
    assert user.name == "Alice"
    assert user.age == 30


@pytest.mark.asyncio
async def test_mixed_keys() -> None:
    d = RMap()

    # Test mixing string and int keys
    await d.set(key="42", value="string answer")
    await d.set(key=42, value="int answer")
    await d.set(key=0, value="zero int")
    await d.set(key="0", value="zero string")

    assert await d.get("42") == "string answer"
    assert await d.get(42) == "int answer"
    assert await d.get(0) == "zero int"
    assert await d.get("0") == "zero string"

    # Test pop with mixed keys
    await d.pop(42)
    assert await d.get(42) is None
    assert await d.get("42") == "string answer"

    await d.pop("0")
    assert await d.get("0") is None
    assert await d.get(0) == "zero int"


@pytest.mark.asyncio
async def test_concurrent_int_keys() -> None:
    d = RMap()

    # Test concurrent set with int keys
    await asyncio.gather(
        d.set(key=1, value="one"),
        d.set(key=2, value=asyncio.Lock()),
        d.set(key=3, value=asyncio.get_running_loop().create_future()),
    )

    # Test concurrent get with int keys
    results = await asyncio.gather(
        d.get(1),
        d.get(2),
        d.get(3),
    )
    assert results[0] == "one"
    assert isinstance(results[1], asyncio.Lock)
    assert isinstance(results[2], asyncio.Future)


@pytest.mark.asyncio
async def test_concurrent_mixed_keys() -> None:
    d = RMap()

    async def set_keys():
        await d.set(key=42, value="int value")
        await d.set(key="42", value="string value")

    async def get_keys():
        int_val = await d.get(42)
        str_val = await d.get("42")
        assert int_val in (None, "int value")
        assert str_val in (None, "string value")

    await asyncio.gather(set_keys(), get_keys(), set_keys(), get_keys())
