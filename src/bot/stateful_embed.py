"""A subclass of discord.Embed that stores a state as JSON in a fake thumbnail URL."""

from __future__ import annotations

import datetime
import logging
import urllib.parse
from abc import ABC
from typing import TYPE_CHECKING, Any, Generic, Self, TypeVar, get_args, get_origin

import discord
import pydantic
from pydantic import BaseModel

if TYPE_CHECKING:
    from discord.types.embed import EmbedType

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class StatefulEmbed(Generic[T], discord.Embed, ABC):
    """An embed that stores a state in the embed itself, and can be retrieved from a message.

    This is done by constructing a fake thumbnail url with the state serialized as JSON as the query string.
    The URL will not point to an image, so it will not be displayed on discord, but it can still be
    retrieved from the message.
    """

    model_class: type[T]

    def __init_subclass__(cls: type[Self], **kwargs: Any) -> None:
        # Set the model_class attribute based on the generic type parameter
        super().__init_subclass__(**kwargs)
        orig_bases: tuple[type, ...] = getattr(cls, "__orig_bases__", ())

        for base in orig_bases:
            origin = get_origin(base)
            if origin is StatefulEmbed:
                cls.model_class = get_args(base)[0]
                break

        if not hasattr(cls, "model_class"):
            raise TypeError(
                f"Class {cls.__name__} must have a generic type parameter to set the model class."
            )

    def __init__(
        self,
        *,
        state: BaseModel | None = None,
        color: int | discord.Colour | None = None,
        title: str | None = None,
        embed_type: EmbedType = "rich",
        url: str | None = None,
        description: str | None = None,
        timestamp: datetime.datetime | None = None,
    ):
        super().__init__(
            color=color,
            title=title,
            type=embed_type,
            url=url,
            description=description,
            timestamp=timestamp,
        )
        self.state = state

    @property
    def state(self) -> BaseModel | None:
        """The state stored in the embed."""
        return self._state

    @state.setter
    def state(self, value: BaseModel | None):
        self._state = value
        self.set_thumbnail(url=self._generate_thumbnail_url())

    def _generate_thumbnail_url(self) -> str:
        """Generate a fake thumbnail url with the state as the query string."""
        base_url = "https://example.com/"

        json_state = self.state.model_dump_json() if self.state else "{}"
        url_encoded = urllib.parse.quote_plus(json_state)

        return f"{base_url}{url_encoded}"

    @classmethod
    def from_message(cls: type[Self], message: discord.Message) -> T | None:
        """Return the state stored in the message's embed thumbnail url.

        Args:
            message: The message to get the state from.

        Returns:
            The state stored in the message's embed thumbnail url, or None if not found or invalid.
        """
        if not message.embeds:
            return None

        embed = message.embeds[0]

        if not embed.thumbnail:
            return None

        url = embed.thumbnail.url

        if not url:
            return None

        unparsed_json = url.replace("https://example.com/", "")

        if not unparsed_json:
            return None

        json_state = urllib.parse.unquote_plus(unparsed_json)

        try:
            model = cls.model_class.model_validate_json(json_state)
        except pydantic.ValidationError:
            logger.error(
                "Invalid state found in message: %s with json returned: %s and expected model: %s",
                message.id,
                json_state,
                cls.model_class.model_fields,
            )
            return None

        return model
