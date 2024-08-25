"""This module contains the User table."""

from piccolo.columns import BigInt, ForeignKey, OnDelete, Text
from piccolo.table import Table

from src.database.tables.pnw import Nation


class RegisteredUser(Table):
    """Stores information about users registered with the bot."""

    discord_id = BigInt(primary_key=True)
    nation = ForeignKey(references=Nation, on_delete=OnDelete.set_null)

    pnw_api_key = Text(null=True)
