"""
Contains the Guild table, which stores settings for each
discord guild which has registered with the bot.
"""

from __future__ import annotations

from piccolo.columns import (
    JSONB,
    UUID,
    Boolean,
    ForeignKey,
    Integer,
    OnDelete,
    Timestamp,
    Varchar,
)
from piccolo.table import Table

# from src.tables.alliance import Alliance


class AllianceSettings(Table):
    """
    A table to store settings for each discord guild which has registered
    """

    alliance = ForeignKey(references="Alliance", on_delete=OnDelete.cascade)
    enable_bank = Boolean(default=False)
    offshore_alliance = ForeignKey(references="Alliance", on_delete=OnDelete.set_null)

    @property
    def custom_roles(self):
        return (
            CustomBotRole.objects()
            .where(CustomBotRole.alliance == self.alliance)
            .first()
        )

    async def create_custom_role(self, name: str, permission_bits: int):
        role = CustomBotRole(
            name=name, alliance=self.alliance, permission_bits=permission_bits
        )
        await role.save()
        return role


class GuildSettings(Table):
    """
    A table to store settings for each discord guild which has registered
    with the bot.
    """

    prefix = Varchar(length=5, null=True)
    alliance = ForeignKey(references=AllianceSettings, on_delete=OnDelete.set_null)
    role_map = JSONB()


class CustomBotRole(Table):
    """
    A table for alliances to map permissions to custom bot roles,
    which can be mapped to discord roles on a per-guild basis.
    """

    id = UUID(primary_key=True)
    name = Varchar(length=50)
    alliance = ForeignKey(references="Alliance", on_delete=OnDelete.cascade)
    permission_bits = Integer()
    created_at = Timestamp(auto_now_add=True)
    updated_at = Timestamp(auto_now=True)
    created_by = ForeignKey(references="User", on_delete=OnDelete.set_null)
