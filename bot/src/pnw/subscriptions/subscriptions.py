import logging
from typing import Any, Awaitable, Callable, Coroutine, Generic, TypeVar

import aiohttp

from src.config import get_settings

from .asyncpusher import Channel, Pusher

logger = logging.getLogger(__name__)

T = TypeVar("T")

Callback = Callable[["T"], Coroutine[Any, Any, Any]]


class Subscription(Generic[T]):
    def __init__(self, pusher: Pusher, name: str, event: str, callbacks: Callback[T]):
        self.pusher = pusher
        self.name = name
        self.event = event
        self.callbacks = callbacks

        self._channel: Channel | None = None

    async def subscribe(self):
        if not self.pusher.connection.is_connected():
            await self.pusher.connect()

        channel_name = await self._get_channel(self.name, self.event)

        if not channel_name:
            logger.error("Could not get channel name for %s %s", self.name, self.event)
            return

        self._channel = await self.pusher.subscribe(channel_name)

        for event_name in self._construct_event_names(self.name, self.event):
            self._channel.bind(event_name, self.callbacks)

        logger.info("Subscribed to %s %s", self.name, self.event)

    async def _get_channel(self, name: str, event: str) -> str | None:
        """Get channel name."""
        url = (
            f"https://api.politicsandwar.com/subscriptions/v1/subscribe/{name}/{event}"
            f"?api_key={get_settings().pnw.api_key}"
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
    def __init__(self, pusher: Pusher):
        self.pusher = pusher

    @property
    def is_connected(self):
        return self.pusher.connection.is_connected()

    async def subscribe(
        self,
        name: str,
        event: str,
        callback: Callable[[str, Any, Any], Awaitable[None]],
    ):
        if not self.is_connected:
            await self.pusher.connect()

        channel_name = await self._get_channel(name, event)

        if not channel_name:
            logger.error("Could not get channel name for %s %s", name, event)
            return

        channel = await self.pusher.subscribe(channel_name)

        for event_name in self._construct_event_names(name, event):
            channel.bind(event_name, callback)

        logger.info("Subscribed to %s %s", name, event)
