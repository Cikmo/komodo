"""Type definitions."""

from typing import Any, Callable, Coroutine

EventData = dict[str, Any] | list[dict[str, Any]] | None
Callback = Callable[..., Coroutine[Any, Any, Any]]
EventCallbacks = dict[str, dict[Callback, tuple[Any, Any]]]
