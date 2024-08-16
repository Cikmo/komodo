"""AI Chatbot."""

from functools import wraps
from logging import getLogger
from typing import Any, Callable

from async_lru import alru_cache
from openai import AsyncOpenAI

import discord
from discord.ext import commands
from src.bot import Bot
from src.config.settings import get_settings

logger = getLogger(__name__)


ASSISTANT_NAME = "Komodo"
ASSISTANT_VERSION = "0.1.0"
ASSISTANT_INSTRUCTIONS_FILE_PATH = "resources/chatbot/ai_instructions.txt"


def should_process_message(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to check if a message should be processed by the chatbot."""

    @wraps(func)
    async def wrapper(
        self: Any, message: discord.Message, *args: Any, **kwargs: Any
    ) -> None:
        if message.author.bot:
            return
        if message.channel.id != get_settings().ai.chatbot_channel_id:
            return
        return await func(self, message, *args, **kwargs)

    return wrapper


class Chatbot(commands.Cog):
    """Cog for the AI chatbot."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.openai = AsyncOpenAI(api_key=get_settings().ai.openai_key)

    @commands.Cog.listener()
    @should_process_message
    async def on_message(self, message: discord.Message):
        """Called when a message is sent in the chatbot channel."""

        if not message.author.id == 267814904226906115:
            return

        await message.channel.send("reponse")

    @alru_cache(maxsize=1)
    async def get_assistant(self):
        """Get the assistant object."""

        # Check if the assistant already exists
        assistants = self.openai.beta.assistants.list()

        async for assistant in assistants:
            if assistant.name == ASSISTANT_NAME:
                # Check if the version matches
                assert isinstance(assistant.metadata, dict)

                if assistant.metadata.get("version") == ASSISTANT_VERSION:
                    return assistant

        # If no assistant is found or version has changed, create a new one
        try:
            with open(ASSISTANT_INSTRUCTIONS_FILE_PATH, "r", encoding="utf-8") as file:
                instructions = file.read()
        except FileNotFoundError as e:
            logger.error("%s not found.", ASSISTANT_INSTRUCTIONS_FILE_PATH)
            raise e

        new_assistant = await self.openai.beta.assistants.create(
            name=ASSISTANT_NAME,
            instructions=instructions,
            tools=[
                {"type": "code_interpreter"},
                {
                    "type": "function",
                    "function": {
                        "name": "get_nation_data",
                        "description": "Get data about a nation in Politics and War."
                        " The nation can be found by name or Discord ID (if linked).",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "nation_name": {
                                    "type": "string",
                                    "description": "The name of the nation. Case insensitive."
                                    " Mutually exclusive with 'discord_id'.",
                                },
                                "discord_name": {
                                    "type": "string",
                                    "description": "The Discord name of a user. Mutually exclusive with 'nation_name'.",
                                },
                            },
                            "additionalProperties": False,
                        },
                    },
                },
                {
                    "type": "function",
                    "function": {
                        "name": "search_for_gif",
                        "description": "Search for a GIF and get a URL to the first result.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "The search query for the GIF.",
                                },
                            },
                            "required": ["query"],
                            "additionalProperties": False,
                        },
                    },
                },
            ],
            model="gpt-4o-mini",
            metadata={
                "version": ASSISTANT_VERSION
            },  # Store the version in the assistant's metadata
        )

        return new_assistant


async def setup(bot: Bot):
    """Called as extension is loaded"""
    await bot.add_cog(Chatbot(bot))
