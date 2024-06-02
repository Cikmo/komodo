"""
Main module of the application.
"""

import asyncio
import logging
import os
import hikari

from src.settings import get_settings

if os.name != "nt":
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

logger = logging.getLogger(__name__)


def main():
    """The entry point of the application."""

    settings = get_settings()

    _bot = hikari.GatewayBot(token=settings.discord.token)
