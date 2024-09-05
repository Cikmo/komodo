"""Pydantic models."""

from typing import Any

import orjson
from pydantic import BaseModel, Field, field_validator

from .types import EventData


class PusherEvent(BaseModel):
    """Pusher event"""

    name: str = Field(alias="event")
    data: EventData = None
    channel: str | None = None

    @field_validator("data", mode="before")
    @classmethod
    def load_json_data(cls, v: str | EventData) -> Any:
        """Load json data from string."""
        if not isinstance(v, str):
            return v

        try:
            return orjson.loads(v)
        except orjson.JSONDecodeError:
            return v


class ConnectionEstablishedEvent(BaseModel):
    """Connection established event"""

    socket_id: str
    activity_timeout: int
