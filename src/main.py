"""
Main module of the application.
"""

import asyncio
import logging
import os

import discord
from discord.ext import commands

from src.bot.bot import Bot
from src.config.logging_conf import setup_logging
from src.config.settings import get_settings

if os.name != "nt":
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

logger = logging.getLogger(__name__)


def main():
    """The entry point of the application."""
    setup_logging()
    run_bot()


def run_bot():
    """Runs the discord bot. Only returns when the bot is stopped."""
    bot = Bot(
        command_prefix=commands.when_mentioned_or(
            get_settings().discord.default_command_prefix
        ),
        intents=get_discord_intents(),
    )

    bot.run(token=get_settings().discord.token, log_handler=None)


def get_discord_intents():
    """Return the intents for the bot."""
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True

    intents.guild_typing = False
    intents.dm_typing = False

    return intents
