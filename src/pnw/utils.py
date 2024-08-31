"""Utility functions for PNW related tasks."""

from datetime import datetime, timedelta, timezone

TURN_CHANGE_DURATION = 1
DAY_CHANGE_DURATION = 10

PRE_TURN_CHANGE_CHECK = 1


def next_turn_change(now: datetime | None = None) -> datetime:
    """Get the next turn change time."""
    if now is None:
        now = datetime.now(timezone.utc)
    next_turn = now.hour + 2 - now.hour % 2
    if next_turn >= 24:
        # Wrap around to the next day
        next_turn = 0
        now += timedelta(days=1)
    return now.replace(hour=next_turn, minute=0, second=0, microsecond=0)


def previous_turn_change(now: datetime | None = None) -> datetime:
    """Get the previous turn change time."""
    if now is None:
        now = datetime.now(timezone.utc)
    previous_turn = now.hour - now.hour % 2
    if previous_turn < 0:
        # Wrap around to the previous day
        previous_turn = 22
        now -= timedelta(days=1)
    return now.replace(hour=previous_turn, minute=0, second=0, microsecond=0)


def is_turn_change_window(now: datetime | None = None) -> timedelta | None:
    """Check if the current time is within a turn change window.

    Args:
        now: The datetime to check. Defaults to the current time in UTC.

    Returns:
        The time remaining until the end of the turn change window, or None if the current time is not within a window.
    """
    if now is None:
        now = datetime.now(timezone.utc)

    next_change = next_turn_change(now)
    previous_change = previous_turn_change(now)

    duration_minutes: int

    if now.hour in (23, 0):
        duration_minutes = DAY_CHANGE_DURATION
    else:
        duration_minutes = TURN_CHANGE_DURATION

    time_until_next_change = next_change - now
    time_since_previous_change = now - previous_change

    if time_until_next_change <= timedelta(minutes=PRE_TURN_CHANGE_CHECK):
        window_end = next_change + timedelta(minutes=duration_minutes)
        return window_end - now

    if time_since_previous_change <= timedelta(minutes=duration_minutes):
        window_end = previous_change + timedelta(minutes=duration_minutes)
        return window_end - now

    return None


def turns_to_datetime(turns: int, now: datetime | None = None) -> datetime:
    """Convert a number of turns to a datetime object.

    Args:
        turns: The number of turns to convert.
        now: The current datetime. Defaults to the current time in UTC.

    Returns:
        The datetime object representing the time in the future when the specified number of turns will pass.
    """
    if now is None:
        now = datetime.now(timezone.utc)

    if turns < 0:
        raise ValueError("turns must be greater than or equal to 0")

    return (now + timedelta(hours=turns * 2)).replace(minute=0, second=0, microsecond=0)


def datetime_to_turns(dt: datetime, now: datetime | None = None):
    """Convert a datetime object to the number of turns until that time.

    Args:
        dt: The datetime to convert.
        now: The current datetime. Defaults to the current time in UTC.

    Returns:
        The number of turns until the specified datetime.
    """
    if not now:
        now = datetime.now(timezone.utc)

    if dt < now:
        # When I have time, add a way to calculate the number of turns in the past
        # This was too hard for my little brain to figure out
        raise ValueError("dt must be in the future")

    dt = dt.replace(minute=0, second=0, microsecond=0)
    now = now.replace(minute=0, second=0, microsecond=0)

    if now.hour % 2 != 0:
        now -= timedelta(hours=1)

    delta = dt - now

    turns = int(delta.total_seconds() / (60 * 60 * 2))

    return turns
