"""Type definitions."""

from typing import Any, Awaitable, Callable

EventData = dict[str, Any] | list[dict[str, Any]] | None
EventCallbacks = dict[str, dict[Callable[..., Awaitable[None]], tuple[Any, Any]]]
