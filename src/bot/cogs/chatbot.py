"""AI Chatbot."""

from functools import wraps
from logging import getLogger
from typing import TYPE_CHECKING, Any, Callable

from async_lru import alru_cache
from openai import AsyncOpenAI
from openai.types import ChatModel
from openai.types.beta.assistant import Assistant
from openai.types.beta.thread import Thread

import discord
from discord.ext import commands
from src.bot import Bot
from src.config.settings import get_settings

if TYPE_CHECKING:
    from openai.types.beta import Thread

logger = getLogger(__name__)

# Constants
ASSISTANT_NAME: str = "Komodo"
ASSISTANT_VERSION: str = "0.1.0"
ASSISTANT_MODEL: ChatModel = "gpt-4o-mini"
ASSISTANT_INSTRUCTIONS_FILE_PATH: str = "resources/chatbot/ai_instructions.txt"


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

        self.threads: dict[int, Thread] = {}

    @commands.Cog.listener()
    @should_process_message
    async def on_message(self, message: discord.Message):
        """Called when a message is sent in the chatbot channel."""

        if not message.author.id == 267814904226906115:
            return

        assistant = await self.get_assistant()

        await message.channel.send(f"assistant: {assistant.id}")

    @alru_cache(maxsize=1)
    async def get_assistant(self) -> Assistant:
        """
        Get or create an OpenAI Assistant object. The function checks if a valid assistant
        with the correct version exists. If not, it creates a new assistant with the given
        instructions.

        Returns:
            Assistant: The assistant object with the correct version.
        Raises:
            FileNotFoundError: If the instructions file is not found.
        """

        # IMPORTANT: Remember to bump the version number if the assistant is changed in any way.

        # Check if the assistant already exists
        assistants = self.openai.beta.assistants.list()
        async for assistant in assistants:
            if assistant.name == ASSISTANT_NAME:
                # Check if the version matches
                if not isinstance(assistant.metadata, dict):
                    continue
                if assistant.metadata.get("version") == ASSISTANT_VERSION:
                    return assistant

        # If no assistant is found or version has changed, create a new one
        try:
            with open(ASSISTANT_INSTRUCTIONS_FILE_PATH, "r", encoding="utf-8") as file:
                instructions = file.read()
        except FileNotFoundError as e:
            logger.error(
                "Assistant instructions file %s not found.",
                ASSISTANT_INSTRUCTIONS_FILE_PATH,
            )
            raise e

        new_assistant = await self.openai.beta.assistants.create(
            name=ASSISTANT_NAME,
            instructions=instructions,
            model="gpt-4o-mini",
            metadata={
                "version": ASSISTANT_VERSION
            },  # Store the version in the assistant's metadata
        )

        logger.info(
            "Created new assistant %s with version %s",
            new_assistant.id,
            ASSISTANT_VERSION,
        )

        return new_assistant

    async def get_thread(self, message: discord.Message) -> Thread:
        """
        Get an OpenAI thread object. If a thread already exists for the channel, return it.
        Otherwise, create a new thread.
        """
        if message.channel.id in self.threads:
            thread = self.threads[message.channel.id]
        else:
            thread = await self.openai.beta.threads.create()
            self.threads[message.channel.id] = thread
        return thread


class ChatbotFunctions:
    """Functions that the AI chatbot can run."""

    def __init__(self, bot: Bot):
        self.bot = bot


async def setup(bot: Bot):
    """Called as extension is loaded"""
    await bot.add_cog(Chatbot(bot))
