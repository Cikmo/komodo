from discord.ext import commands, tasks

from src.bot import Bot


class TestTask(commands.Cog):
    """A test cog for testing tasks."""

    def __init__(self, bot: Bot):
        self.bot = bot

        self.index = 0

    @commands.Cog.listener()
    async def on_ready(self):
        """Called when the bot is ready."""
        self.printer.start()

    async def cog_unload(self):
        self.printer.cancel()

    @tasks.loop(seconds=5.0, count=5)
    async def printer(self):
        """Prints a message every 10 seconds."""
        self.index += 1


async def setup(bot: Bot):
    """Called as extension is loaded"""
    await bot.add_cog(TestTask(bot))
