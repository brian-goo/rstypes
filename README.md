
# rstypes

`rstypes` is a minimal Python package providing **thread-safe**, **async-aware** data types implemented in **Rust**. It is designed for high-performance concurrent and asynchronous programming in Python.

This library is ideal for building:
- ✅ **Global or shared dictionaries** across threads or async tasks
- ✅ **In-memory async-aware caches** with TTL support

Internally, each instance uses a single **mutex**, not per-key locks, keeping locking semantics simple and predictable.

## Features

- 🧵 **Thread-safe**: Types that can be safely used across multiple threads.
- ⚡ **Async-aware**: Compatible with `asyncio` and async/await patterns
- 🚀 **Rust-powered**: Built with [PyO3](https://github.com/PyO3/pyo3) for blazing-fast native performance
- 🔐 **Default value support**: Behaves like `collections.defaultdict`

## Installation

```bash
pip install rstypes
```

## Example Usage

### 🔹 Minimal Example

```python
import asyncio

from rstypes import RMap

async def main():
    d = RMap()
    await d.set(key="hello", value=123)
    val = await d.get("hello")
    assert val == 123

    await d.set(key=7, value="answer")
    await d.pop(7)
    val = await d.get(7)
    assert val is None
    
asyncio.run(main())
```

### 🔹 Async `defaultdict` Behavior

```python
import asyncio

from rstypes import RMap

async def main():
    rlock = RMap(asyncio.Lock) # like defaultdict(asyncio.Lock)
    
    async with await rlock.get("mykey"):
        print("Inside an asyncio.Lock")

asyncio.run(main())
```

### 🔹 Memory Cache with TTL

```python
import asyncio
from typing import NamedTuple

from rstypes import RCacheMap

class Foo(NamedTuple):
    name: str
    age: int

async def main():
    cache = RCacheMap()

    await cache.set(key="hello", value=123, ttl=1.0)  # 1 second TTL
    await cache.set(key="user", value=Foo(name="Alice", age=30), ttl=2.0)  # 2 seconds TTL

    await cache.pop("hello")
    assert await cache.get("hello") is None

    user = await cache.get("user")
    assert isinstance(user, Foo)

    await asyncio.sleep(2.1)
    await cache.pop_expired()
    assert await cache.get("user") is None

asyncio.run(main())
```

## License

`rstypes` is licensed under the MIT License. See [LICENSE](LICENSE) for more information.

