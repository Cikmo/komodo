"""A custom view with additional functionality. Views should inherit from this class."""

from __future__ import annotations

import logging
from typing import Self

import discord

logger = logging.getLogger(__name__)


class PersistentView(discord.ui.View):
    """A custom view with additional functionality. Views should inherit from this class."""

    def __init__(self, *, timeout: float | None = None):
        super().__init__(timeout=timeout)

    @property
    def with_disabled_components(self) -> Self:
        """Returns a copy of the view with all components disabled."""
        new_view = self.__class__()
        for child in new_view.children:
            if isinstance(child, (discord.ui.Button, discord.ui.Select)):
                child.disabled = True
        return new_view

    async def disable_components(self, interaction: discord.Interaction):
        """Disable all components in the view on the interacted on message.

        Args:
            interaction: The interaction that triggered the view.
        """
        if not interaction.message:
            return

        await interaction.message.edit(view=self.with_disabled_components)
