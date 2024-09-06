"""
This module contains the Subscription class, which represents a subscription to a PnW event.
"""

import logging
from typing import Any, Callable, Coroutine, TypeVar

import aiohttp

from .asyncpusher import Channel, Pusher

logger = logging.getLogger(__name__)

T = TypeVar("T")

Callback = Callable[[Any], Coroutine[Any, Any, Any]]


class Subscription:
    """
    Represents a subscription to a PnW event.
    """

    def __init__(
        self,
        pusher: Pusher,
        pnw_api_key: str,
        name: str,
        event: str,
        callbacks: list[Callback],
    ):
        self._pusher = pusher
        self._pnw_api_key = pnw_api_key

        self.name = name
        self.event = event
        self.callbacks = callbacks

        self._channel: Channel | None = None

    @property
    def is_subscribed(self) -> bool:
        """Check if the subscription is active."""
        return bool(self._channel)

    def add_callback(self, callback: Callback) -> None:
        """Add a callback to the subscription.

        Args:
            callback: The callback to add.
        """
        self.callbacks.append(callback)

    async def start(self):
        """Subscribe to a model in PnW.

        Returns:
            The subscription object if successful. None otherwise.
        """
        if self.is_subscribed:
            return self

        if not self._pusher.connection.is_connected():
            await self._pusher.connect()

        channel_name = await self._get_channel(self.name, self.event)

        if not channel_name:
            logger.error("Could not get channel name for %s %s", self.name, self.event)
            return

        self._channel = await self._pusher.subscribe(channel_name)

        for event_name in self._construct_event_names(self.name, self.event):
            self._channel.bind(event_name, self._callback)

        logger.info("Subscribed to %s %s", self.name, self.event)

        return self

    async def _callback(self, data: Any):
        for callback in self.callbacks:
            await callback(data)

    async def _get_channel(self, name: str, event: str) -> str | None:
        """Get channel name."""
        url = (
            f"https://api.politicsandwar.com/subscriptions/v1/subscribe/{name}/{event}"
            f"?api_key={self._pnw_api_key}"
        )

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                # try to get "channel" from response jason
                return (await response.json()).get("channel")

    def _construct_event_names(self, name: str, event: str) -> tuple[str, str]:
        name = name.upper()
        event = event.upper()

        return f"{name}_{event}", f"BULK_{name}_{event}"


class Subscriptions:
    """
    Manages subscriptions to PnW events.
    """

    def __init__(self, pusher: Pusher, pnw_api_key: str):
        self._pusher = pusher
        self._pnw_api_key = pnw_api_key

        self.subscriptions: dict[str, Subscription] = {}

    async def subscribe(
        self, name: str, event: str, *callbacks: Callback
    ) -> Subscription:
        """Subscribe to a PnW event.

        Args:
            name: The name of the model to subscribe to.
            event: The event to subscribe to.
            callbacks: The callbacks to call when the event is triggered.

        Returns:
            The subscription object.
        """
        subscription = Subscription(
            self._pusher, self._pnw_api_key, name, event, list(callbacks)
        )
        self.subscriptions[f"{name}_{event}"] = subscription

        await subscription.start()

        return subscription

    async def unsubscribe(self, subscription: Subscription) -> None:
        """Unsubscribe from a PnW event.

        Args:
            subscription: The subscription to unsubscribe from.
        """
        if not subscription.is_subscribed:
            return

        await self._pusher.unsubscribe(subscription._channel._name)  # type: ignore # pylint: disable=protected-access

        del self.subscriptions[f"{subscription.name}_{subscription.event}"]
        subscription._channel = None  # type: ignore # pylint: disable=protected-access
        logger.info("Unsubscribed from %s %s", subscription.name, subscription.event)

    def get(self, name: str, event: str) -> Subscription | None:
        """Get a subscription by name and event.

        Args:
            name: The name of the model.
            event: The event.

        Returns:
            The subscription if it exists. None otherwise.
        """
        return self.subscriptions.get(f"{name}_{event}")
