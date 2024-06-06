"""
Developer commands
"""

from discord.ext import commands

from src.bot import Bot
from src.tables import Nation


class Developer(commands.Cog):
    """Developer commands."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.group(name="dev", aliases=["!"])
    @commands.is_owner()
    async def dev(self, ctx: commands.Context[Bot]):
        """Group for developer commands."""
        pass

    @dev.command()
    async def create(self, ctx: commands.Context[Bot], name: str):
        """Ping the bot."""
        nation = await Nation.objects().get(Nation.name == name)

        if nation:
            await ctx.reply("Nation already exists.")
            return

        nation = Nation(name=name)
        await nation.save()
        await ctx.reply(f"Created nation {name}")

    @dev.command()
    async def get(self, ctx: commands.Context[Bot], name: str):
        """Ping the bot."""
        nation = await Nation.objects().get(Nation.name == name)

        if not nation:
            await ctx.reply("Nation does not exist.")
            return

        await ctx.reply(f"Found nation {name}")

    @dev.command()
    async def reload(self, ctx: commands.Context[Bot], cog_name: str):
        """Reload a cog by name."""
        try:
            await self.bot.reload_cog(cog_name)
            await ctx.reply(f"Reloaded cog {cog_name}")
        except commands.ExtensionNotFound:
            await ctx.reply(f"Could not find cog {cog_name}")
        except commands.ExtensionNotLoaded:
            await ctx.invoke(self.load, cog_name=cog_name)

    @dev.command()
    async def load(self, ctx: commands.Context[Bot], cog_name: str):
        """Load a cog by name."""
        try:
            await self.bot.load_cog(cog_name)
            await ctx.reply(f"Loaded cog {cog_name}")
        except commands.ExtensionNotFound:
            await ctx.reply(f"Could not find cog {cog_name}")
        except commands.ExtensionAlreadyLoaded:
            await ctx.reply(f"Cog {cog_name} is already loaded")

    @dev.command()
    async def unload(self, ctx: commands.Context[Bot], cog_name: str):
        """Unload a cog by name."""
        try:
            await self.bot.unload_cog(cog_name)
            await ctx.reply(f"Unloaded cog {cog_name}")
        except commands.ExtensionNotFound:
            await ctx.reply(f"Could not find cog {cog_name}")
        except commands.ExtensionNotLoaded:
            await ctx.reply(
                f"Cog {cog_name} is not loaded, so it cannot be unloaded. Dumbass."
            )


async def setup(bot: Bot):
    await bot.add_cog(Developer(bot))
