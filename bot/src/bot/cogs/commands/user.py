"""
Developer commands
"""

from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING

import discord
from discord.ext import commands
from src.database.tables.pnw import Nation
from src.discord.utils import TimestampType, create_discord_timestamp

if TYPE_CHECKING:
    from src.bot import Bot


class User(commands.Cog):
    """For user specific commands like registering and user settings."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.hybrid_command()
    async def whoo(self, ctx: commands.Context[Bot], nation_name: str):
        """Get information about a user."""
        nation = await Nation.objects().where(Nation.name.ilike(nation_name)).first()

        if not nation:
            return await ctx.send("Nation not found.")

        alliance = await nation.get_related(Nation.alliance)

        message = f"# [{nation.name}](https://politicsandwar.com/nation/id={nation.id})"

        embed = discord.Embed(
            description=dedent(
                f"""
                **Leader:** {nation.leader_name}
                **Alliance:** {alliance.name if alliance else "None"}
                **Color:** {nation.color}
                **Cities:** {nation.num_cities}
                **Projects:** {nation.num_projects}
                **Last Active:** {create_discord_timestamp(nation.last_active, TimestampType.RELATIVE_TIME)}
                """
            ),
        )

        await ctx.send(message, embed=embed)


async def setup(bot: Bot):
    """Called as extension is loaded"""
    await bot.add_cog(User(bot))
