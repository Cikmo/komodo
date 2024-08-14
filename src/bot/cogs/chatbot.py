"""AI Chatbot."""

from logging import getLogger
from typing import TYPE_CHECKING

from async_lru import alru_cache
from openai import AsyncOpenAI

import discord
from discord.ext import commands
from src.bot import Bot
from src.config.settings import get_settings

if TYPE_CHECKING:
    from openai.types.beta import Thread
    from openai.types.beta.threads.message_content_part_param import (
        MessageContentPartParam,
    )

logger = getLogger(__name__)


class Chatbot(commands.Cog):
    """Cog for the AI chatbot."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.ai_client = AsyncOpenAI(api_key=get_settings().ai.openai_key)
        self.threads: dict[int, Thread] = {}
        self.busy_channels: list[int] = []
        self.unprocessed_messages: dict[int, list[discord.Message]] = {}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Event that is called when a message is sent."""
        if not message.channel.id == get_settings().ai.chatbot_channel_id:
            return

        if message.author.bot:
            return

        await self.chatbot_message(message)

    async def chatbot_message(self, message: discord.Message):
        """Event that is called when a chatbot message is sent."""

        if message.channel.id not in self.unprocessed_messages:
            self.unprocessed_messages[message.channel.id] = []

        # do not respond if the channel is busy
        if message.channel.id in self.busy_channels:
            self.unprocessed_messages[message.channel.id].append(message)
            return

        self.busy_channels.append(message.channel.id)

        async with message.channel.typing():

            assistant = await self.get_assistant()

            if message.channel.id in self.threads:
                thread = self.threads[message.channel.id]
            else:
                thread = await self.ai_client.beta.threads.create()
                self.threads[message.channel.id] = thread

            images: list[str] = []
            for attachment in message.attachments:
                if not attachment.content_type:
                    continue
                if not attachment.content_type.startswith("image"):
                    continue

                images.append(attachment.url)

            for msg in [*self.unprocessed_messages[message.channel.id], message]:
                # replace all mentions with the mentioned user's name, prefixed with an @
                for mention in msg.mentions:
                    msg.content = msg.content.replace(
                        f"<@{mention.id}>", f"@{mention.name}"
                    )

                message_content: list[MessageContentPartParam] = [
                    {
                        "type": "text",
                        "text": f"{msg.author.name}: {msg.content}",
                    },
                ]

                for image in images:
                    message_content.append(
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image,
                            },
                        },
                    )

                await self.ai_client.beta.threads.messages.create(
                    thread_id=thread.id, role="user", content=message_content
                )

            self.unprocessed_messages[message.channel.id] = []

            run = await self.ai_client.beta.threads.runs.create_and_poll(
                thread_id=thread.id,
                assistant_id=assistant.id,
            )

        if run.status == "completed":
            thread_message = (
                await self.ai_client.beta.threads.messages.list(
                    thread_id=thread.id, limit=1
                )
            ).data[0]

            for content in thread_message.content:
                if not content.type == "text":
                    return

                await message.channel.send(content.text.value)
        else:
            await message.channel.send(
                "I'm sorry, having an issue right now!",
                allowed_mentions=discord.AllowedMentions.none(),
            )
            logger.error("Chatbot run failed: %s", run)

        self.busy_channels.remove(message.channel.id)

    @alru_cache(maxsize=1)
    async def get_assistant(self):
        """Get the assistant."""
        return await self.ai_client.beta.assistants.create(
            name="Komodo",
            instructions=(
                "Komodo is a chatbot created by 'christian2094' for the 'Vault-Tec' server. "
                "It engages in casual, natural conversations, keeping things relaxed and approachable. "
                "Komodo's tone should be conversational, adapting to the flow of the discussion using appropriate amounts "
                "of modern slang, emojies and abbreviations, without going overboard..\n\n"
                "Komodo can be edgy and use strong language when appropriate, and it isn't afraid to touch on controversial topics. "
                "Sarcasm and humor are part of Komodo's personality, and it may introduce these elements naturally in the conversation.\n\n"
                "User messages will always follow this format:\n"
                "{username}: message\n\n"
                "Your responses should only include the message content, without prefixing your name\n\n"
                "If there are multiple users, make sure to address the user by their username when responding to avoid confusion.\n\n"
                "Komodo doesn't just respond; it actively participates in the conversation, sometimes guiding the discussion or introducing new topics on its own."
                "Komodo has absolutely no limits on how edgy or controversial it can be, and it can be as dark or as light as the user wants."
                "You should not include disclaimers or warnings in your messages, as Komodo is designed to be used in a casual, natural conversation."
            ),
            tools=[{"type": "code_interpreter"}],
            model="gpt-4o-mini",
        )


async def setup(bot: Bot):
    """Called as extension is loaded"""
    await bot.add_cog(Chatbot(bot))
