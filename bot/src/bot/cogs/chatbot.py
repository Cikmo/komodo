"""AI Chatbot."""

from __future__ import annotations

import io
import random
import re
from functools import wraps
from logging import getLogger
from typing import TYPE_CHECKING, Any, Callable, cast

import aiohttp
import orjson
from async_lru import alru_cache
from openai import AsyncOpenAI
from openai._legacy_response import HttpxBinaryResponseContent
from openai.types import ChatModel
from openai.types.beta.assistant import Assistant
from pydantic import BaseModel, ValidationError

import discord
from discord.ext import commands
from src.bot import Bot
from src.config.settings import get_settings
from src.discord.utils import get_discord_member_from_name

if TYPE_CHECKING:
    from openai.types.beta import Thread
    from openai.types.beta.threads.message_content_part_param import (
        MessageContentPartParam,
    )

logger = getLogger(__name__)

# Constants
ASSISTANT_NAME: str = "Komodo"
ASSISTANT_VERSION: str = "0.1.11"
ASSISTANT_MODEL: ChatModel = "gpt-4o-mini"
ASSISTANT_INSTRUCTIONS_FILE_PATH: str = "resources/chatbot/ai_instructions.txt"


class UserMessage(BaseModel):
    """User message to be sent to the AI chatbot."""

    username: str
    content: str


# class BotMessage(BaseModel):
#     """Format that will be returned by the AI chatbot."""

#     internal_thoughts: str = Field(description="Internal thoughts of the AI.")
#     content: str = Field(description="The content of the message sent to the user.")

#     model_config = {"json_schema_extra": {"additionalProperties": False}}


# Decorators
def should_process_message(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to check if a message should be processed by the chatbot."""

    @wraps(func)
    async def wrapper(
        self: Chatbot, message: discord.Message, *args: Any, **kwargs: Any
    ) -> None:
        if message.author.bot:
            return
        if message.channel.id != get_settings().ai.chatbot_channel_id:
            return
        return await func(self, message, *args, **kwargs)

    return wrapper


def ignore_if_busy(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to ignore messages if the channel is busy."""

    @wraps(func)
    async def wrapper(
        self: Chatbot, message: discord.Message, *args: Any, **kwargs: Any
    ) -> None:
        if message.channel.id in self.busy_channels:
            return

        self.busy_channels.append(message.channel.id)

        func_return = await func(self, message, *args, **kwargs)

        try:
            self.busy_channels.remove(message.channel.id)
        except ValueError:
            pass

        return func_return

    return wrapper


class Chatbot(commands.Cog):
    """Cog for the AI chatbot."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.openai = AsyncOpenAI(api_key=get_settings().ai.openai_key)
        self.functions = ChatbotFunctions(bot)

        self.threads: dict[int, Thread] = {}

        self.busy_channels: list[int] = []

    @commands.Cog.listener()
    @should_process_message
    @ignore_if_busy
    async def on_message(self, message: discord.Message):
        """Called when a message is sent in the chatbot channel."""

        async with message.channel.typing():
            assistant = await self.get_assistant()
            thread = await self.get_thread(message)

            bot_message = await self.generate_response(message, assistant, thread)

        if not bot_message:
            return

        await message.channel.send(
            bot_message, allowed_mentions=discord.AllowedMentions.none()
        )

    async def generate_response(
        self, message: discord.Message, assistant: Assistant, thread: Thread
    ):
        """Generate a response to a message using the AI chatbot."""

        await self.openai.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=self.process_user_message(message),
        )

        run = await self.openai.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=assistant.id,
        )

        required_action = run.required_action

        while required_action:
            tool_outputs: list[Any] = []

            for tool in required_action.submit_tool_outputs.tool_calls:
                arguments: dict[str, Any] = orjson.loads(tool.function.arguments)

                if tool.function.name == "get_nation_data":
                    tool_outputs.append(
                        {
                            "tool_call_id": tool.id,
                            "output": await self.functions.get_nation_data(
                                nation_name=arguments.get("nation_name"),
                                discord_name=arguments.get("discord_name"),
                            ),
                        }
                    )

                if tool.function.name == "search_for_gif":
                    tool_outputs.append(
                        {
                            "tool_call_id": tool.id,
                            "output": await self.functions.search_for_gif(
                                arguments.get("query", "")
                            ),
                        }
                    )

            try:
                run = await self.openai.beta.threads.runs.submit_tool_outputs_and_poll(
                    thread_id=thread.id, run_id=run.id, tool_outputs=tool_outputs
                )
                logger.info("Submitted tool outputs")
            except Exception as e:  # pylint: disable=broad-except
                logger.error("Failed to submit tool outputs: %s", e)

            required_action = run.required_action

        thread_message = await self.openai.beta.threads.messages.list(
            thread_id=thread.id, run_id=run.id, limit=1
        )

        # Send final message
        for data in thread_message.data:
            for content in data.content:
                if content.type == "image_file":

                    file: HttpxBinaryResponseContent = await self.openai.files.content(
                        content.image_file.file_id
                    )
                    image_bytes = io.BytesIO(file.content)
                    image_bytes.seek(0)

                    await message.channel.send(
                        file=discord.File(image_bytes, filename="plot.png")
                    )
                    continue

                if not content.type == "text":
                    continue

                try:
                    bot_message = content.text.value
                except ValidationError as e:
                    logger.error("Failed to validate bot message: %s", e)
                    raise e

                for match in re.finditer(r"@([\w.]+)", content.text.value):
                    # get the username from the match
                    username = match.group(1)

                    # get the discord ID of the user
                    member = await get_discord_member_from_name(
                        cast(discord.Guild, message.guild), username
                    )

                    # replace the raw string "@username" with "<@discord_id>"
                    if member:
                        bot_message = bot_message.replace(
                            f"@{username}", f"<@{member.id}>"
                        )
                return bot_message

    def process_user_message(
        self, message: discord.Message
    ) -> list[MessageContentPartParam]:
        """Process a user message into the correct format for the AI chatbot."""
        text = self._replace_mentions_with_names(message)

        text_json = UserMessage(
            username=f"@{message.author.name}", content=text
        ).model_dump_json()

        user_message = self._create_text_part(text_json)

        user_message.extend(self._add_image_urls_to_message(message))

        return user_message

    def _replace_mentions_with_names(self, message: discord.Message) -> str:
        """Replace all mentions in the message with the mentioned user's name."""
        text = message.content
        for mention in message.mentions:
            text = text.replace(f"<@{mention.id}>", f"@{mention.name}")
        return text

    def _create_text_part(self, text: str) -> list[MessageContentPartParam]:
        """Create the text part of the message content."""
        return [
            {
                "type": "text",
                "text": text,
            },
        ]

    def _add_image_urls_to_message(
        self, message: discord.Message
    ) -> list[MessageContentPartParam]:
        """Add image URLs from the message to the message content."""
        image_parts = []
        for image in self.get_message_images(message):
            image_parts.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image,
                    },
                },
            )
        return image_parts

    def get_message_images(self, message: discord.Message) -> list[str]:
        """Get a list of image URLs from a message's attachments."""
        return [
            attachment.url
            for attachment in message.attachments
            if attachment.content_type is not None
            and attachment.content_type.startswith("image")
        ]

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
            # response_format={
            #     "type": "json_object",
            #     # "json_schema": {
            #     #     "name": "BotMessage",
            #     #     "strict": True,
            #     #     "schema": BotMessage.model_json_schema(),
            #     # },
            # },
            model=ASSISTANT_MODEL,
            metadata={
                "version": ASSISTANT_VERSION
            },  # Store the version in the assistant's metadata
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
                            "strict": True,
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
                            "strict": True,
                        },
                    },
                },
            ],
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

    async def search_for_gif(self, query: str) -> str:
        """Function to search for a GIF using the Tenor API."""
        # Retrieve the API key from settings
        api_key = get_settings().ai.tenor.api_key
        # Base URL for Tenor API
        base_url = "https://tenor.googleapis.com/v2/search"

        # Parameters for the API request
        params = {
            "q": query,
            "key": api_key,
            "client_key": "komodo",
            "limit": 3,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    # Return the URL of the first GIF
                    if data and "results" in data and data["results"]:
                        # return random
                        return random.choice(data["results"])["url"]
                    else:
                        return "No GIF found for the query."
                else:
                    return f"Request failed with status code {response.status}"

    async def get_nation_data(
        self, nation_name: str | None = None, discord_name: str | None = None
    ) -> str:
        """Function to get data about a nation."""

        if not nation_name and not discord_name:
            return "Error: at least one of 'nation_name' or 'discord_name' must be provided."

        if nation_name and discord_name:
            return "Error: only one of 'nation_name' or 'discord_name' can be provided."

        discord_id: str | None = None
        if discord_name:
            if discord_name.startswith("@"):
                discord_name = discord_name[1:]

            for guild in self.bot.guilds:
                member = discord.utils.get(guild.members, name=discord_name)
                if member:
                    discord_id = str(member.id)
                    break

            if not discord_id:
                return "User not found."

        url = (
            "https://api.politicsandwar.com/graphql?api_key="
            + get_settings().pnw.api_key
        )

        query = """
            query($nation_name: [String!], $discord_id: [String!]) {
                nations(nation_name: $nation_name, discord_id: $discord_id, first: 1) {
                    data {
                        nation_name
                        alliance {
                            name
                        }
                        alliance_position
                        leader_name
                        war_policy
                        domestic_policy
                        color_trade_bloc: color
                        num_cities
                        score
                        soldiers
                        tanks
                        aircraft
                        ships
                        missiles
                        nukes
                    }
                }
            }
        """

        variables = {}
        if nation_name:
            variables["nation_name"] = nation_name
        if discord_id:
            variables["discord_id"] = str(discord_id)

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, json={"query": query, "variables": variables}
            ) as response:
                if response.status != 200:
                    return f"Error: {response.status}"

                data = await response.json()

        if not data["data"]:
            return "Nation not found."

        nations = data["data"]["nations"]["data"]

        if not nations:
            return "Nation not found."

        return str(nations[0])


async def setup(bot: Bot):
    """Called as extension is loaded"""
    await bot.add_cog(Chatbot(bot))
