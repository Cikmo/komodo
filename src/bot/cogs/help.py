"""
This extension provides a custom help command for the bot.
"""

### Guide: https://gist.github.com/InterStella0/b78488fb28cadf279dfd3164b9f0cf96

from typing import Any, Mapping

import discord
from discord.ext import commands

from src.bot import Bot


class MyHelp(commands.MinimalHelpCommand):
    """Custom help command for the bot."""

    async def send_bot_help(
        self,
        mapping: Mapping[commands.Cog | None, list[commands.Command[Any, ..., Any]]],
        /,
    ):
        """Send help for the bot.

        Args:
            mapping: A mapping of cogs to their commands.
        """

        embed = discord.Embed(title="Help")

        # List cogs
        cogs: list[str] = []
        for cog, cog_commands in mapping.items():
            # skip if the cog is Help
            if cog_commands:
                cog_name = getattr(cog, "qualified_name", "Miscellaneous")
                if cog_name == "Help":
                    continue
                if cog:
                    cogs.append(f"- {cog_name}")

        embed.add_field(name="Categories", value="\n".join(cogs), inline=True)

        await self.context.send(embed=embed)


class Help(commands.Cog):
    """Help command for the bot."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self._original_help_command = bot.help_command

        help_command = MyHelp(command_attrs={"aliases": ["??"]})
        help_command.cog = self
        bot.help_command = help_command

    async def cog_unload(self):
        self.bot.help_command = self._original_help_command


async def setup(bot: Bot):
    """Called as extension is loaded."""
    await bot.add_cog(Help(bot))
