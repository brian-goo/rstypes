import asyncio

from rstypes import RMap


async def main():
    rmap = RMap()

    await rmap.set("key1", "value1")
    await rmap.set("key2", "value2")

    await rmap.set(42, "value3")
    await rmap.set(100, "value4")

    keys = await rmap.keys()
    print("Initial keys:", keys)

    values = await rmap.values()
    print("Initial values:", values)

    for k in await rmap.keys():
        if k == "key1":
            await rmap.set(key=k, value="new_value1")
        print(k, await rmap.get(k))

    await rmap.pop("key1")
    keys = await rmap.keys()
    print("Keys after removing 'key1':", keys)

    values = await rmap.values()
    print("Values after removing 'key1':", values)


if __name__ == "__main__":
    asyncio.run(main())
