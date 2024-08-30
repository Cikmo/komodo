"""Utility functions for PNW related tasks."""

from datetime import datetime, timedelta, timezone

TURN_CHANGE_DURATION = 1
DAY_CHANGE_DURATION = 10


def remaining_turn_change_duration(now: datetime | None = None) -> timedelta | None:
    """Check if the current time is within a turn change window. Triggers 1 minute preemptively.

    Args:
        now: The datetime to check. Defaults to the current time in UTC.

    Returns:
        The remaining duration until the next turn change, or None if no turn change is occurring.
    """
    # Shift time by 1 minute into the future to account for preemptive triggering
    if not now:
        now = datetime.now(timezone.utc) + timedelta(minutes=1)

    # Check if it's the start of a new day (UTC midnight)
    if now.hour == 0:
        if now.minute < (DAY_CHANGE_DURATION + 1):
            remaining_duration = timedelta(
                minutes=(DAY_CHANGE_DURATION + 1 - now.minute)
            )
            return remaining_duration

    # Check if it's a regular turn change (every even hour)
    if now.hour % 2 == 0 and now.minute < (TURN_CHANGE_DURATION + 1):
        remaining_duration = timedelta(minutes=TURN_CHANGE_DURATION + 1 - now.minute)
        return remaining_duration

    # If no turn change is occurring
    return None


def next_turn_change() -> datetime:
    """Get the next turn change time."""
    now = datetime.now(timezone.utc)
    next_hour = now.hour + 2 - now.hour % 2
    return now.replace(hour=next_hour, minute=0, second=0, microsecond=0)


def turns_to_datetime(turns: int) -> datetime:
    """Convert the number of turns to a datetime object."""
    return datetime.now(timezone.utc) + timedelta(hours=turns * 2)
