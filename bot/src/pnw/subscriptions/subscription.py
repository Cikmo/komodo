"""
This module contains the Subscription class, which represents a subscription to a PnW event.
"""

from __future__ import annotations

import asyncio
import logging
from enum import StrEnum, auto
from typing import Any, Generic, Iterable, Literal, TypeVar, overload

import aiohttp
from pydantic import BaseModel

from ..api_v3 import SubscriptionAccountFields, SubscriptionNationFields
from .asyncpusher import Channel, Pusher
from .asyncpusher.types import Callback

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=SubscriptionAccountFields | SubscriptionNationFields)


class MetadataTime(BaseModel):
    """Metadata time."""

    millis: int
    nanos: int

    def __eq__(self, other: Any):
        if isinstance(other, MetadataTime):
            return (self.millis, self.nanos) == (other.millis, other.nanos)
        return NotImplemented

    def __lt__(self, other: Any):
        if isinstance(other, MetadataTime):
            return (self.millis, self.nanos) < (other.millis, other.nanos)
        return NotImplemented

    def __gt__(self, other: Any):
        if isinstance(other, MetadataTime):
            return (self.millis, self.nanos) > (other.millis, other.nanos)
        return NotImplemented

    def __le__(self, other: Any):
        return self == other or self < other

    def __ge__(self, other: Any):
        return self == other or self > other


class MetadataEvent(BaseModel):
    """Metadata event."""

    after: MetadataTime
    max: MetadataTime
    crc32: int


class SubscriptionModel(StrEnum):
    """Subscription models."""

    NATION = auto()
    ACCOUNT = auto()
    CITY = auto()


class SubscriptionEvent(StrEnum):
    """Subscription events."""

    CREATE = auto()
    UPDATE = auto()
    DELETE = auto()


class Subscription(Generic[T]):
    """
    Represents a subscription to a PnW event.
    """

    subscribe_lock = asyncio.Lock()
    _unsubscribe_lock = asyncio.Lock()

    def __init__(
        self,
        pusher: Pusher,
        pnw_api_key: str,
        model: SubscriptionModel,
        event: SubscriptionEvent,
        data_model: type[T],
        callbacks: list[Callback],
    ):
        """Create a new subscription.

        Args:
            pusher: The Pusher object.
            pnw_api_key: The PnW API key.
            model: The model to subscribe to.
            event:
            data_model: A Pydantic model representing the data that will be passed to the callbacks.
            callbacks: The callbacks to call when the event is triggered.
        """
        self._pusher = pusher
        self._pnw_api_key = pnw_api_key

        self.model = model
        self.event = event
        self.callbacks = callbacks
        self.data_model = data_model

        self._channel: Channel | None = None

        self._cached_metadata: MetadataEvent | None = None

        self._turn_change_check_interval = 10

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

    async def _subscribe(self, since: tuple[int, int] | None = None):
        """Subscribe to a model in PnW.

        Returns:
            The subscription object if successful. None otherwise.
        """
        async with self.subscribe_lock:
            if self.is_subscribed:
                return

            await self._pusher.connect()

            channel_name = await self._get_channel(since)

            if not channel_name:
                logger.error(
                    "Could not get channel name for %s %s",
                    self.model.value,
                    self.event.value,
                )
                return

            self._channel = await self._pusher.subscribe(channel_name)

            for event_name in self._construct_event_names(self.model, self.event):
                self._channel.bind(event_name, self._callback)
                self._channel.bind(f"{event_name}_METADATA", self._handle_metadata)

            logger.info("Subscribed to %s %s", self.model, self.event)

    async def _unsubscribe(self):
        """Unsubscribe from a model in PnW."""
        if not self.is_subscribed:
            return

        await self._pusher.unsubscribe(self._channel._name)  # type: ignore # pylint: disable=protected-access

        self._channel = None

    async def _callback(self, data: dict[str, Any] | list[dict[str, Any]]):
        for callback in self.callbacks:
            if isinstance(data, list):
                for item in data:
                    await callback(self.data_model(**item))
            else:
                await callback(self.data_model(**data))

    async def _handle_metadata(self, data: Any):
        new_metadata = MetadataEvent(**data)

        if not self._cached_metadata:
            self._cached_metadata = new_metadata
            return

        # If the new metadata is newer than the cached metadata,
        # we missed some events and need to rollback
        if self._cached_metadata.max < new_metadata.after:
            logger.info(
                "Missed events for %s %s. Rolling back...", self.model, self.event
            )
            logger.info(
                "Cached metadata: %s, New metadata: %s",
                self._cached_metadata,
                new_metadata,
            )
            await self._unsubscribe()
            await self._subscribe(
                (
                    self._cached_metadata.max.millis,
                    self._cached_metadata.max.nanos - 1,
                )
            )
            return

        self._cached_metadata = new_metadata

    async def _get_channel(
        self,
        since: tuple[int, int] | None = None,
    ) -> str | None:
        """Get the channel name for the subscription.

        Args:
            fields: If provided, the fields to include in the returned data. Defaults to all fields.
            since: If provided, the time to get events since. Max 10 minutes.

        Returns:
            The channel name if successful. None otherwise.
        """
        # get the field names (or alias if it exists) from the BaseModel as a comma-separated string

        fields = ",".join(
            x.alias if x.alias else field_name
            for field_name, x in self.data_model.model_fields.items()
        )

        url = (
            f"https://api.politicsandwar.com/subscriptions/v1/subscribe/{self.model.value}/{self.event.value}"
            f"?api_key={self._pnw_api_key}&metadata=true"
            f"&include={fields}"
        )
        if since:
            url += f"&since={since[0]}&nanos={since[1]}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return (await response.json()).get("channel")

    def _construct_event_names(
        self, model: SubscriptionModel, event: SubscriptionEvent
    ) -> tuple[str, str]:
        model_str = model.value.upper()
        event_str = event.value.upper()

        return f"{model_str}_{event_str}", f"BULK_{model_str}_{event_str}"


class Subscriptions:
    """
    Manages subscriptions to PnW events.
    """

    def __init__(self, pnw_api_key: str):
        self._pusher = Pusher(
            "a22734a47847a64386c8",
            custom_host="socket.politicsandwar.com",
            auth_endpoint="https://api.politicsandwar.com/subscriptions/v1/auth",
            auto_sub=True,
            max_msg_size=0,  # no limit
        )
        self._pnw_api_key = pnw_api_key

        self.subscriptions: dict[str, Subscription[Any]] = {}

    @overload
    async def subscribe(
        self,
        model: Literal[SubscriptionModel.NATION],
        event: SubscriptionEvent,
        callbacks: Iterable[Callback],
    ) -> Subscription[SubscriptionNationFields]: ...

    @overload
    async def subscribe(
        self,
        model: Literal[SubscriptionModel.ACCOUNT],
        event: SubscriptionEvent,
        callbacks: Iterable[Callback],
    ) -> Subscription[SubscriptionAccountFields]: ...

    @overload
    async def subscribe(
        self,
        model: SubscriptionModel,
        event: SubscriptionEvent,
        callbacks: Iterable[Callback],
    ) -> Subscription[Any]: ...

    async def subscribe(
        self,
        model: SubscriptionModel,
        event: SubscriptionEvent,
        callbacks: Iterable[Callback],
    ) -> Subscription[Any]:
        """Subscribe to a PnW event.

        Args:
            model: The name of the model to subscribe to.
            event: The event to subscribe to.
            callbacks: The callbacks to call when the event is triggered.

        Returns:
            The subscription object.
        """
        if f"{model.value}_{event.value}" in self.subscriptions:
            logger.warning(
                "Tried to subscribe to %s %s, but already subscribed",
                model.value,
                event.value,
            )
            return self.subscriptions[f"{model.value}_{event.value}"]

        match model:
            case SubscriptionModel.NATION:
                data_model = SubscriptionNationFields
            case SubscriptionModel.ACCOUNT:
                data_model = SubscriptionAccountFields
            case _:
                raise NotImplementedError(f"Model {model} not implemented")

        subscription = Subscription(
            self._pusher, self._pnw_api_key, model, event, data_model, list(callbacks)
        )
        self.subscriptions[f"{model.value}_{event.value}"] = subscription

        await subscription._subscribe()  # type: ignore # pylint: disable=protected-access

        return subscription

    async def unsubscribe(self, subscription: Subscription[Any]) -> None:
        """Unsubscribe from a PnW event.

        Args:
            subscription: The subscription to unsubscribe from.
        """
        if not subscription in self.subscriptions.values():
            return

        await subscription._unsubscribe()  # type: ignore # pylint: disable=protected-access

        del self.subscriptions[f"{subscription.model.value}_{subscription.event.value}"]
        logger.info(
            "Unsubscribed from %s %s",
            subscription.model.value,
            subscription.event.value,
        )

    def get(
        self, model: SubscriptionModel, event: SubscriptionEvent
    ) -> Subscription[Any] | None:
        """Get a subscription by name and event.

        Args:
            name: The name of the model.
            event: The event.

        Returns:
            The subscription if it exists. None otherwise.
        """
        return self.subscriptions.get(f"{model.value}_{event.value}")
