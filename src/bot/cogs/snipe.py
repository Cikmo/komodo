import logging
import re
from datetime import datetime

import discord
from discord.ext import commands
from pydantic import BaseModel

from src.bot import Bot
from src.utils import create_discord_timestamp

logger = logging.getLogger(__name__)


class MessageDeleted(BaseModel):
    message_content: str
    message_author_id: int
    time_sent: datetime
    time_deleted: datetime


class MessageEdited(BaseModel):
    message_id: int
    message_content_before: str
    message_content_after: str
    message_author_id: int
    time_sent: datetime
    time_edited: datetime


class Snipe(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.snipes: dict[int, MessageDeleted | MessageEdited] = {}

    def sanitise(self, text: str):
        if len(text) > 1024:
            text = text[0:1021] + "..."

        invite_re = r"(http[s]?:\/\/)*discord((app\.com\/invite)|(\.gg))\/(invite\/)?(#\/)?([A-Za-z0-9\-]+)(\/)?"
        text = re.sub(invite_re, "[INVITE REDACTED]", text)
        return text

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot:
            return

        self.snipes[message.channel.id] = MessageDeleted(
            message_content=message.content,
            message_author_id=message.author.id,
            time_sent=message.created_at,
            time_deleted=datetime.now(),
        )

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot:
            return

        self.snipes[before.channel.id] = MessageEdited(
            message_id=before.id,
            message_content_before=before.content,
            message_content_after=after.content,
            message_author_id=before.author.id,
            time_sent=before.created_at,
            time_edited=datetime.now(),
        )

    @commands.hybrid_command()
    async def snipe(self, ctx: commands.Context[Bot]):
        """Snipe the last deleted message in the channel."""

        assert ctx.guild is not None

        message = self.snipes.pop(ctx.channel.id, None)

        if message is None:
            return await ctx.send("There is nothing to snipe.")

        if isinstance(message, MessageDeleted):
            sanitised_content = self.sanitise(message.message_content)
            embed = discord.Embed(
                title="Message Deleted",
                description=(
                    f"`Sent:    ` {create_discord_timestamp(message.time_deleted)}\n"
                    f"`Deleted: ` {create_discord_timestamp(message.time_deleted)}"
                ),
                colour=discord.Colour.blurple(),
            )

            embed.add_field(name="Content", value=sanitised_content, inline=False)

        else:
            before_sanitised = self.sanitise(message.message_content_before)
            after_sanitised = self.sanitise(message.message_content_after)

            embed_description = ""

            embed_description = (
                f"https://discord.com/channels/{ctx.guild.id}/{ctx.channel.id}/{message.message_id}\n"
                f"`Sent:    ` {create_discord_timestamp(message.time_sent)}\n"
                f"`Edited: ` {create_discord_timestamp(message.time_edited)}"
            )

            embed = discord.Embed(
                title="Message Edited",
                description=embed_description,
                colour=discord.Colour.blurple(),
            )

            embed.add_field(name="Before", value=before_sanitised, inline=False)
            embed.add_field(name="After", value=after_sanitised, inline=False)

        embed.set_footer(text=f"Sniped by {ctx.author}")

        author = ctx.bot.get_user(message.message_author_id)

        if author is not None:
            embed.set_author(
                name=author,
                icon_url=(
                    author.avatar.url if author.avatar else author.default_avatar.url
                ),
            )
        else:
            embed.set_author(
                name="Unknown User",
                icon_url="https://cdn.discordapp.com/embed/avatars/0.png",
            )

        await ctx.send(embed=embed)


async def setup(bot: Bot):
    await bot.add_cog(Snipe(bot))
