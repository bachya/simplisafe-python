"""Define utility modules."""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any, Optional

# pylint: disable=consider-alternative-union-syntax
CallbackType = Callable[..., Optional[Awaitable[None]]]


def execute_callback(callback: CallbackType, *args: Any) -> None:
    """Schedule a callback to be called.

    The callback is expected to be short-lived, as no sort of task management takes
    place – this is a fire-and-forget system.

    Args:
        callback: The callback to execute.
        *args: Any arguments to pass to the callback.
    """
    if asyncio.iscoroutinefunction(callback):
        asyncio.create_task(callback(*args))
    else:
        callback(*args)
