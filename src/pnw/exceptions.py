"""Exceptions related to PNW API"""


class TooCloseToTurnChange(Exception):
    """Raised when a turn change is too close to the current time."""

    pass
