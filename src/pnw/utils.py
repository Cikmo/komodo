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


def turns_to_datetime(turns: int) -> datetime:
    """Convert the number of turns to a datetime object."""
    return datetime.now(timezone.utc) + timedelta(hours=turns * 2)


# THIS DOES NOT FUCKING WORK, FIX IT
def datetime_to_turns(dt: datetime, now: datetime | None = None):
    """Convert a datetime object to the number of turns."""
    # Get the current time
    if not now:
        now = datetime.now()

    # Calculate the difference in hours between now and the target datetime
    total_seconds = (dt - now).total_seconds()
    total_hours = total_seconds // 3600

    # Calculate the full even hours that would fall between now and the target datetime
    if total_hours > 0:
        # Moving forward in time
        start_hour = (
            (now.hour // 2 + 1) * 2
            if now.minute > 0 or now.second > 0
            else now.hour + 2
        )
        end_hour = (dt.hour // 2) * 2
        return max(0, (end_hour - start_hour) // 2 + 1)
    else:
        # Moving backward in time
        start_hour = (now.hour // 2) * 2
        end_hour = (dt.hour // 2 + 1) * 2 if dt.minute > 0 or dt.second > 0 else dt.hour
        return max(0, (start_hour - end_hour) // 2 + 1)
