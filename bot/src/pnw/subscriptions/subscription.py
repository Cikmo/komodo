"""
This module contains the Subscription class, which represents a subscription to a PnW event.
"""

from __future__ import annotations

import asyncio
import logging
from enum import Enum, StrEnum, auto
from typing import Any, Literal, Sequence, cast, overload

import aiohttp
from pydantic import BaseModel

from ..api_v3 import (
    SubscriptionAccountFields,
    SubscriptionAllianceFields,
    SubscriptionAlliancePositionFields,
    SubscriptionCityFields,
    SubscriptionNationFields,
)
from .asyncpusher import Channel, Pusher
from .asyncpusher.types import Callback

logger = logging.getLogger(__name__)

type SubscriptionFields = (
    SubscriptionAccountFields
    | SubscriptionNationFields
    | SubscriptionAllianceFields
    | SubscriptionAlliancePositionFields
    | SubscriptionCityFields
)


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


# class SubscriptionModel(StrEnum):
#     """Subscription models."""

#     NATION = auto()
#     ACCOUNT = auto()
#     CITY = auto()
#     ALLIANCE = auto()
#     ALLIANCE_POSITION = auto()


class SubscriptionModel(Enum):
    """Subscription models."""

    NATION = SubscriptionNationFields
    ACCOUNT = SubscriptionAccountFields
    CITY = SubscriptionCityFields
    ALLIANCE = SubscriptionAllianceFields
    ALLIANCE_POSITION = SubscriptionAlliancePositionFields

    @property
    def model_name(self):
        """The model name used in the API."""
        return self.name.lower()


class SubscriptionEvent(StrEnum):
    """Subscription events."""

    CREATE = auto()
    UPDATE = auto()
    DELETE = auto()

    @classmethod
    def all(cls):
        """Get all subscription events."""
        return list(cls)


class Subscription:
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
                    self.model.model_name,
                    self.event.value,
                )
                return

            self._channel = await self._pusher.subscribe(channel_name)

            for event_name in self._construct_event_names(self.model, self.event):
                self._channel.bind(event_name, self._callback)
                self._channel.bind(f"{event_name}_METADATA", self._handle_metadata)

            logger.info("Subscribed to %s %s", self.model.model_name, self.event)

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
                    await callback(self.model.value(**item))
            else:
                await callback(self.model.value(**data))

    async def _handle_metadata(self, data: Any):
        new_metadata = MetadataEvent(**data)

        if not self._cached_metadata:
            self._cached_metadata = new_metadata
            return

        # If the new metadata is newer than the cached metadata,
        # we missed some events and need to rollback
        if self._cached_metadata.max < new_metadata.after:
            logger.info(
                "Missed events for %s %s. Rolling back...",
                self.model.model_name,
                self.event,
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
            for field_name, x in self.model.value.model_fields.items()
        )

        url = (
            f"https://api.politicsandwar.com/subscriptions/v1/subscribe/{self.model.model_name}/{self.event.value}"
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
        model_str = model.model_name.upper()
        event_str = event.value.upper()

        return f"{model_str}_{event_str}", f"BULK_{model_str}_{event_str}"


class Subscriptions:
    """
    Manages subscriptions to PnW events.
    """

    def __init__(
        self, pnw_api_key: str, last_subscription_event: tuple[int, int] | None = None
    ):
        self._pusher = Pusher(
            "a22734a47847a64386c8",
            custom_host="socket.politicsandwar.com",
            auth_endpoint="https://api.politicsandwar.com/subscriptions/v1/auth",
            auto_sub=True,
            max_msg_size=0,  # no limit
        )
        self._pnw_api_key = pnw_api_key
        self._last_subscription_event = last_subscription_event

        self.subscriptions: dict[str, Subscription] = {}

    async def subscribe(
        self,
        model: SubscriptionModel,
        event: SubscriptionEvent,
        callbacks: Sequence[Callback],
    ) -> Subscription:
        """Subscribe to a PnW event.

        Args:
            model: The name of the model to subscribe to.
            event: The event to subscribe to.
            callbacks: The callbacks to call when the event is triggered.

        Returns:
            The subscription object.
        """
        if f"{model.model_name}_{event.value}" in self.subscriptions:
            logger.warning(
                "Tried to subscribe to %s %s, but already subscribed",
                model.model_name,
                event.value,
            )
            return self.subscriptions[f"{model.model_name}_{event.value}"]

        # data_model = self.get_data_model(model)

        subscription = Subscription(
            self._pusher, self._pnw_api_key, model, event, list(callbacks)
        )
        self.subscriptions[f"{model.model_name}_{event.value}"] = subscription

        await subscription._subscribe()  # type: ignore # pylint: disable=protected-access

        return subscription

    async def unsubscribe(self, subscription: Subscription) -> None:
        """Unsubscribe from a PnW event.

        Args:
            subscription: The subscription to unsubscribe from.
        """
        if not subscription in self.subscriptions.values():
            return

        await subscription._unsubscribe()  # type: ignore # pylint: disable=protected-access

        del self.subscriptions[
            f"{subscription.model.model_name}_{subscription.event.value}"
        ]
        logger.info(
            "Unsubscribed from %s %s",
            subscription.model.model_name,
            subscription.event.value,
        )

    def get(
        self, model: SubscriptionModel, event: SubscriptionEvent
    ) -> Subscription | None:
        """Get a subscription by name and event.

        Args:
            name: The name of the model.
            event: The event.

        Returns:
            The subscription if it exists. None otherwise.
        """
        return self.subscriptions.get(f"{model.model_name}_{event.value}")

    @overload
    async def fetch_subscriptions_snapshot(
        self, model: Literal[SubscriptionModel.NATION]
    ) -> list[SubscriptionNationFields]: ...

    @overload
    async def fetch_subscriptions_snapshot(
        self, model: Literal[SubscriptionModel.ACCOUNT]
    ) -> list[SubscriptionAccountFields]: ...

    @overload
    async def fetch_subscriptions_snapshot(
        self, model: Literal[SubscriptionModel.ALLIANCE]
    ) -> list[SubscriptionAllianceFields]: ...

    @overload
    async def fetch_subscriptions_snapshot(
        self, model: Literal[SubscriptionModel.ALLIANCE_POSITION]
    ) -> list[SubscriptionAlliancePositionFields]: ...

    @overload
    async def fetch_subscriptions_snapshot(
        self, model: Literal[SubscriptionModel.CITY]
    ) -> list[SubscriptionCityFields]: ...

    @overload
    async def fetch_subscriptions_snapshot(
        self, model: SubscriptionModel
    ) -> Sequence[SubscriptionFields]: ...

    async def fetch_subscriptions_snapshot(
        self, model: SubscriptionModel
    ) -> Sequence[SubscriptionFields]:
        """Get a snapshot of the full game of a model.

        Args:
            model: The model to get a snapshot of.
        """
        endpoint = f"https://api.politicsandwar.com/subscriptions/v1/snapshot/{model.model_name}?api_key={self._pnw_api_key}"

        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint) as response:
                data = await response.json()

        # type of data will be a list of dicts with the model fields.
        # We will need to convert this to a list of the model objects
        try:
            if not isinstance(data, list):
                raise ValueError(f"Expected data to be a list, got {type(data)}")
        except ValueError:
            logger.error("Error fetching snapshot for %s. Data: %s", model.model_name, data)  # type: ignore
            return []

        data = cast(list[dict[str, Any]], data)

        object_list = [model.value(**item) for item in data]

        return object_list
