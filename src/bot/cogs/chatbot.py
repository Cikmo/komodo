"""AI Chatbot."""

import discord
from discord.ext import commands
from src.bot import Bot


class Chatbot(commands.Cog):
    """Cog for the AI chatbot."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Event that is called when a message is sent."""
        assert self.bot.user is not None

        if not self.bot.user.mentioned_in(message):
            return

        if message.author.bot:
            return

        await self.chatbot_message(message)

    async def chatbot_message(self, message: discord.Message):
        """Event that is called when a chatbot message is sent."""
        message_text = message.content
        # replace mentions with the mentioned user's name
        for mention in message.mentions:
            message_text = message_text.replace(f"<@{mention.id}>", f"@{mention.name}")

        await message.channel.send(f"User: {message_text}")


async def setup(bot: Bot):
    """Called as extension is loaded"""
    await bot.add_cog(Chatbot(bot))
