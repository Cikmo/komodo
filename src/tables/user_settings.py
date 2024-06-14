"""This module contains the User table."""

from piccolo.columns import BigInt, ForeignKey, Text
from piccolo.table import Table

from src.tables.pnw import Nation


class UserSettings(Table):
    """Stores information about users registered with the bot."""

    discord_id = BigInt(primary_key=True)
    nation = ForeignKey(references=Nation)

    pnw_api_key = Text(null=True)
