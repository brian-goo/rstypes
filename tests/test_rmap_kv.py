import pytest

from rstypes import RMap


@pytest.mark.asyncio
async def test_rmap_keys_values_items():
    rmap = RMap()

    d = {
        "key1": "value1",
        "key2": "value2",
        42: "value3",
        100: "value4",
    }

    for k, v in d.items():
        await rmap.set(k, v)

    keys = await rmap.keys()
    assert len(keys) == 4
    assert "key1" in keys
    assert "key2" in keys
    assert 42 in keys
    assert 100 in keys

    values = await rmap.values()
    assert len(values) == 4
    assert "value1" in values
    assert "value2" in values
    assert "value3" in values
    assert "value4" in values

    items = await rmap.items()
    assert len(items) == 4
    for k, v in items:
        assert d[k] == v


@pytest.mark.asyncio
async def test_rmap_update_and_pop():
    rmap = RMap()

    await rmap.set(key="key1", value="value1")
    await rmap.set(key="key2", value="value2")

    await rmap.set(key="key1", value="new_value1")
    assert await rmap.get("key1") == "new_value1"

    await rmap.pop("key1")
    assert await rmap.get("key1") is None

    keys = await rmap.keys()
    assert len(keys) == 1
    assert "key2" in keys
    assert "key1" not in keys


@pytest.mark.asyncio
async def test_rmap_iter_and_update():
    rmap = RMap()

    d = {
        "key1": "value1",
        "key2": "value2",
        42: "value3",
    }

    for k, v in d.items():
        await rmap.set(key=k, value=v)

    for k in await rmap.keys():
        if k == "key1":
            await rmap.set(key=k, value="new_value1")
        else:
            assert await rmap.get(k) == d[k]

    assert await rmap.get("key1") == "new_value1"

    await rmap.set(key="key1", value="value1")
    for v in await rmap.values():
        assert v in d.values()

    for k, v in await rmap.items():
        await rmap.set(key=k, value=f"{v}_n")
        assert await rmap.get(k) == f"{v}_n"
