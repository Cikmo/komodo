"""AI Chatbot."""

import json
import random
import re
from logging import getLogger
from typing import TYPE_CHECKING, Any

import aiohttp
from async_lru import alru_cache
from openai import AsyncOpenAI

import discord
from discord import AllowedMentions
from discord.ext import commands
from src.bot import Bot
from src.config.settings import get_settings

if TYPE_CHECKING:
    from openai.types.beta import Thread
    from openai.types.beta.threads.message_content_part_param import (
        MessageContentPartParam,
    )

logger = getLogger(__name__)


async def search_for_gif(query: str) -> str:
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
        "limit": 3,  # Limiting to 1 to get the first result
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
    *, bot: Bot, nation_name: str | None = None, discord_name: str | None = None
) -> str:
    """Function to get data about a nation."""

    if not nation_name and not discord_name:
        return (
            "Error: at least one of 'nation_name' or 'discord_name' must be provided."
        )

    if nation_name and discord_name:
        return "Error: only one of 'nation_name' or 'discord_name' can be provided."

    discord_id: str | None = None
    if discord_name:
        discord_id = await get_discord_id(bot, discord_name)

    url = "https://api.politicsandwar.com/graphql?api_key=" + get_settings().pnw.api_key

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


async def get_discord_id(bot: Bot, discord_name: str) -> str | None:
    """Function to get the Discord ID of a user."""

    discord_name = discord_name.strip()

    for guild in bot.guilds:
        member = discord.utils.get(guild.members, name=discord_name)
        if member:
            return str(member.id)

    return None


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

            did_run_tools: bool = False

            if run.status == "completed":
                thread_messages = await self.ai_client.beta.threads.messages.list(
                    thread_id=thread.id
                )
            else:
                logger.warning("run status: %s", run.status)

            # Define the list to store tool outputs
            tool_outputs: list[Any] = []

            # Loop through each tool in the required action section
            if run.required_action:
                for tool in run.required_action.submit_tool_outputs.tool_calls:
                    arguments: dict[str, Any] = json.loads(tool.function.arguments)

                    if tool.function.name == "get_nation_data":
                        tool_outputs.append(
                            {
                                "tool_call_id": tool.id,
                                "output": await get_nation_data(
                                    bot=self.bot,
                                    nation_name=arguments.get("nation_name"),
                                    discord_name=arguments.get("discord_name"),
                                ),
                            }
                        )

                    if tool.function.name == "search_for_gif":
                        tool_outputs.append(
                            {
                                "tool_call_id": tool.id,
                                "output": await search_for_gif(
                                    arguments.get("query", "")
                                ),
                            }
                        )

            # Submit all tool outputs at once after collecting them in a list
            if tool_outputs:
                did_run_tools = True
                try:
                    run = await self.ai_client.beta.threads.runs.submit_tool_outputs_and_poll(
                        thread_id=thread.id, run_id=run.id, tool_outputs=tool_outputs
                    )
                    print("Tool outputs submitted successfully.")
                except Exception as e:
                    print("Failed to submit tool outputs:", e)
                else:
                    print("No tool outputs to submit.")

        if run.status == "completed":
            if not did_run_tools:
                thread_messages = thread_messages.data[0]  # type: ignore
            else:
                thread_messages = (
                    await self.ai_client.beta.threads.messages.list(
                        thread_id=thread.id, limit=1
                    )
                ).data[0]

            for content in thread_messages.content:
                if not content.type == "text":
                    return

                value = content.text.value

                # replace all raw string "@username" with "<@discord_id>"
                # use regex to find all occurrences of "@username" in the string
                for match in re.finditer(r"@(\w+)", value):
                    # get the username from the match
                    username = match.group(1)

                    # get the discord ID of the user
                    discord_id = await get_discord_id(self.bot, username)

                    # replace the raw string "@username" with "<@discord_id>"
                    if discord_id:
                        value = value.replace(f"@{username}", f"<@{discord_id}>")

                await message.channel.send(
                    value, allowed_mentions=AllowedMentions.none()
                )

        self.busy_channels.remove(message.channel.id)

    @alru_cache(maxsize=1)
    async def get_assistant(self):
        """Get the assistant."""

        instructions_file_path = "resources/chatbot/ai_instructions.txt"

        try:
            with open(instructions_file_path, "r", encoding="utf-8") as file:
                instructions = file.read()
        except FileNotFoundError as e:
            logger.error("%s not found.", instructions_file_path)
            raise e

        return await self.ai_client.beta.assistants.create(
            name="Komodo",
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
                                    "description": "The name of the nation. Case insensitive. Mutually exclusive with 'discord_id'.",
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
                        "description": "Search for a GIF. Useful for when you want to add some visual flair to the conversation.",
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
        )


async def setup(bot: Bot):
    """Called as extension is loaded"""
    await bot.add_cog(Chatbot(bot))
