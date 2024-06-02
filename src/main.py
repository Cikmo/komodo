"""
Main module of the application.
"""

import asyncio
import logging
import os

import discord
from discord.ext import commands

from src.bot import Bot
from src.settings import get_settings
from src.logging import setup_logging

if os.name != "nt":
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

logger = logging.getLogger(__name__)


def main():
    """The entry point of the application."""

    setup_logging()

    settings = get_settings()

    bot = Bot(
        command_prefix=commands.when_mentioned_or(settings.discord.command_prefix),
        intents=discord.Intents.all(),
    )

    bot.run(token=settings.discord.token, log_handler=None)
