"""Define utility modules."""
import asyncio
from typing import Any, Callable


def execute_callback(callback: Callable[..., Any], *args: Any) -> None:
    """Schedule a callback to be called."""
    if asyncio.iscoroutinefunction(callback):
        asyncio.create_task(callback(*args))
    else:
        callback(*args)
