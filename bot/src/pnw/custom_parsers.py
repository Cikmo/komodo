"""
Parsers for custom scalar types in the graphql schema. Used by ariadne-codegen.
"""

import datetime


def parse_nuke_date(x: str) -> datetime.date | None:
    """Parse a date string from a NukeDate."""
    if x.startswith("-"):
        return None

    return datetime.date.fromisoformat(x)


def serialize_nuke_date(x: datetime.date | None) -> str:
    """Serialize a date string for a NukeDate."""
    if x is None:
        return "-0001-11-30"

    return x.strftime("%Y-%m-%d")
