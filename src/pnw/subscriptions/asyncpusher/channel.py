"""Channel module for asyncpusher."""

import logging
from collections import defaultdict
from enum import Enum
from typing import Any, Awaitable, Callable

from .connection import Connection
from .models import PusherEvent
from .types import EventData


class Channel:
    """Represents a channel in pusher."""

    class State(Enum):
        """Channel states"""

        UNSUBSCRIBED = 1
        SUBSCRIBED = 2
        FAILED = 3

    def __init__(
        self,
        name: str,
        connection: Connection,
        log: logging.Logger,
    ):
        self._name = name
        self._connection = connection
        self._log = log

        self._event_callbacks = defaultdict(dict)
        self.state = self.State.UNSUBSCRIBED

        self.bind("pusher_internal:subscription_succeeded", self._handle_success)

    def bind(
        self,
        event_name: str,
        callback: Callable[..., Awaitable[None]],
        *args: Any,
        **kwargs: Any,
    ):
        """Bind a callback to an event.

        Args:
            event_name: Event name to bind to.
            callback: Callback to call when event is triggered.
        """
        self._event_callbacks[event_name][callback] = (args, kwargs)

    def unbind(self, event_name: str, callback: Callable[..., Awaitable[None]]):
        """Unbind a callback from an event.

        Args:
            event_name: Event name to unbind from.
            callback: Callback to unbind.
        """
        del self._event_callbacks[event_name][callback]

    async def handle_event(self, event_name: str, data: EventData):
        """Handle an event on the channel.

        Args:
            event_name: Name of the event.
            data: Data of the event.
        """
        if event_name not in self._event_callbacks:
            self._log.warning(
                f"Unhandled event, channel: {self._name}, event: {event_name}, data: {data}"
            )
            return

        for callback, (args, kwargs) in self._event_callbacks[event_name].items():
            try:
                await callback(data, *args, **kwargs)
            except Exception:  # pylint: disable=broad-except
                self._log.exception(f"Exception in callback: {data}")

    async def trigger(self, event: PusherEvent):
        """Trigger a client event on the channel.

        Args:
            event: Event to trigger.
        """

        if not event.name.startswith("client-"):
            raise ValueError("Client event has to start with client-")

        if not self.is_private() and not self.is_presence():
            raise ValueError(
                "Client event can only be sent on private or presence channels"
            )

        event.channel = self._name
        await self._connection.send_event(event)

    def is_private(self):
        """Check if channel is private."""
        return self._name.startswith("private-")

    def is_presence(self):
        """Check if channel is presence."""
        return self._name.startswith("presence-")

    async def _handle_success(self, _: Any):
        self.state = self.State.SUBSCRIBED
