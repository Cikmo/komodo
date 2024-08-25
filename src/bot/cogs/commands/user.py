"""
Developer commands
"""

from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING

from discord.ext import commands
from src.bot.converters import NationAPIModelConverter

# from src.tables.pnw import Nation
# from src.tables.user_settings import UserSettings
from src.database.tables.pnw import Nation
from src.database.tables.registered_user import RegisteredUser

if TYPE_CHECKING:
    from src.bot import Bot
    from src.pnw.api_v3 import NationFields


async def get_nation_from_discord_id(ctx: commands.Context[Bot]) -> NationFields | None:
    """Get a single nation from a discord id. This is a helper function to
    give the register command a default value."""
    nations = (
        await ctx.bot.api_v3.get_nations(discord_id=[str(ctx.author.id)])
    ).nations.data
    return nations[0] if nations else None


class User(commands.Cog):
    """For user specific commands like registering and user settings."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command()
    async def register(
        self,
        ctx: commands.Context[Bot],
        nation: NationFields | None = commands.parameter(
            converter=NationAPIModelConverter, default=get_nation_from_discord_id
        ),
    ):
        """Register your nation with the bot."""

        if not nation:
            await ctx.reply(
                "Nation not found. Make sure you have the correct nation name or ID."
            )
            return

        print(nation.date)

        nation_db = await Nation.objects().where(Nation.id == int(nation.id)).first()
        if not nation_db:
            nation_db = Nation.from_api_v3(nation)
            await nation_db.save()

        if not nation.discord == ctx.author.name:
            await ctx.reply(
                dedent(
                    f"""
                        The discord username `{nation.discord}` does not match your username `{ctx.author.name}`.
                        
                        **In order to register, please follow these steps:**
                        1. Go to: https://politicsandwar.com/nation/edit/
                        2. Scroll down to where it says Discord Username:
                        3. Enter your Discord username `{ctx.author.name}`
                        4. Save changes
                        5. Run this command again
                        """
                )
            )
            return

        user = (
            await RegisteredUser.objects()
            .where(RegisteredUser.discord_id == ctx.author.id)
            .first()
        )
        if not user:
            user = RegisteredUser(discord_id=ctx.author.id, nation=nation_db)
            await user.save()
        else:
            await ctx.reply("You are already registered ;)")
            return

        await ctx.reply(
            f"Welcome, {nation_db.name}. You have successfully registered!.\n\nFor more info do `!??`"
        )


async def setup(bot: Bot):
    """Called as extension is loaded"""
    await bot.add_cog(User(bot))
