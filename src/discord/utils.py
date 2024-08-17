"""A module for utility functions."""

from datetime import datetime
from enum import StrEnum

import discord


class TimestampType(StrEnum):
    """A class to represent the different formats of timestamps."""

    SHORT_TIME = "t"
    LONG_TIME = "T"
    SHORT_DATE = "d"
    LONG_DATE = "D"
    SHORT_DATE_TIME = "f"
    LONG_DATE_TIME = "F"
    RELATIVE_TIME = "R"


def create_discord_timestamp(
    dt: datetime, timestamp_type: TimestampType = TimestampType.SHORT_DATE_TIME
) -> str:
    """Create a Discord timestamp from a datetime object

    Args:
        dt: The datetime object to convert. Discord assumes UTC.
        timestamp_type: The type of timestamp to create.

    Returns:
        str: The Discord timestamp string.
    """
    return f"<t:{int(dt.timestamp())}:{timestamp_type.value}>"


async def get_discord_member_from_name(
    guild: discord.Guild, discord_name: str
) -> discord.Member | None:
    """Get a Discord member from a guild by their name.

    Args:
        guild: The guild to search in
        discord_name: The name of the user to search for.

    Returns:
        The member if found, otherwise None.
    """
    return discord.utils.get(guild.members, name=discord_name.strip())
