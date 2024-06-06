"""A module for utility functions."""

from datetime import datetime
from enum import StrEnum


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
