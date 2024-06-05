"""
Custom bot class that extends discord.ext.commands.Bot.
"""

import asyncio
import logging
import os
import pathlib
import sys
from typing import Generator

import discord
from discord.ext import commands
from piccolo.engine import PostgresEngine, engine_finder

logger = logging.getLogger(__name__)

COG_PATH = "src/cogs"


class Bot(commands.Bot):
    """Custom bot class that extends discord.ext.commands.Bot."""

    async def setup_hook(self):

        await open_database_connection_pool()

        await load_all_cogs(self)

    async def on_ready(self):
        """Event that is called when the bot is ready."""
        assert self.user is not None
        logger.info("Logged in as %s (ID: %s)", self.user, self.user.id)

        if os.environ.get("RESTART_CHANNEL_ID"):
            channel = self.get_channel(int(os.environ["RESTART_CHANNEL_ID"]))
            if channel and (
                isinstance(channel, discord.TextChannel)
                or isinstance(channel, discord.DMChannel)
                or isinstance(channel, discord.GroupChannel)
                or isinstance(channel, discord.Thread)
            ):
                await channel.send(content="Restarted!")
                del os.environ["RESTART_CHANNEL_ID"]

    async def load_cog(self, cog_name: str):
        """Load a cog by name.

        Args:
            cog_name: The name of the cog to load.

        Raises:
            commands.ExtensionNotFound: If the cog could not be found.
        """
        try:
            module = find_cog_module(cog_name, COG_PATH)
            logger.info("Loaded cog %s", module)
            await self.load_extension(module)
        except FileNotFoundError as e:
            raise commands.ExtensionNotFound(cog_name) from e

    async def unload_cog(self, cog_name: str):
        """Unload a cog by name.

        Args:
            cog_name: The name of the cog to unload.

        Raises:
            commands.ExtensionNotFound: If the cog could not be found.
        """
        try:
            module = find_cog_module(cog_name, COG_PATH)
            logger.info("Unloaded cog %s", module)
            await self.unload_extension(module)
        except FileNotFoundError as e:
            raise commands.ExtensionNotFound(cog_name) from e

    async def reload_cog(self, cog_name: str):
        """Reload a cog by name.

        Args:
            cog_name: The name of the cog to reload.

        Raises:
            commands.ExtensionNotFound: If the cog could not be found.
        """
        try:
            module = find_cog_module(cog_name, COG_PATH)
            logger.info("Reloaded cog %s", module)
        except FileNotFoundError as e:
            raise commands.ExtensionNotFound(cog_name) from e

    async def shutdown(self, restart: bool = False):
        """Shutdown the bot.

        Args:
            restart: Whether to restart the bot after shutting down.
        """
        await close_database_connection_pool()

        await self.close()
        logger.info("Closed bot.")

        if restart:
            os.execv(sys.executable, [sys.executable, *sys.argv])
        else:
            sys.exit(0)


async def open_database_connection_pool():
    """Open the database connection pool."""
    engine: PostgresEngine | None = engine_finder()  # type: ignore
    if not engine:
        raise RuntimeError("No piccolo engine found.")
    await engine.start_connection_pool()
    logger.info("Opened database connection pool.")


async def close_database_connection_pool():
    """Close the database connection pool."""
    engine: PostgresEngine | None = engine_finder()  # type: ignore
    if not engine:
        raise RuntimeError("No piccolo engine found.")
    await engine.close_connection_pool()
    logger.info("Closed database connection pool.")


def find_cog_module(cog_name: str, cog_path: str) -> str:
    """Find a cog's module path from its name. Can match partial names as well.

    Args:
        cog_name: The name of the cog to find.
        cog_path: The base directory where cogs are located.

    Raises:
        FileNotFoundError: If the cog could not be found.

    Returns:
        The path to the cog's module.
    """
    cog_name = cog_name.lower().replace(" ", "_")
    path = pathlib.Path(cog_path)
    module = next((m for m in recursive_module_search(path) if cog_name in m), None)

    if not module:
        raise FileNotFoundError(f"`{cog_name}` cog not found.")

    return module


async def load_all_cogs(bot: Bot) -> None:
    """Load all cogs in the cogs directory. Subdirectories are also searched.

    Args:
        bot: Bot to load cogs into.
    """
    try:
        async with asyncio.TaskGroup() as tg:
            for file in recursive_module_search(pathlib.Path(COG_PATH)):
                tg.create_task(bot.load_extension(file))
                logger.info("Loaded cog %s", file)
    except* commands.errors.ExtensionAlreadyLoaded as eg:
        for e in eg.exceptions:
            logger.warning(e)
    except* commands.errors.ExtensionNotFound as eg:
        for e in eg.exceptions:
            logger.warning(e)
    except* commands.errors.NoEntryPointError as eg:
        for e in eg.exceptions:
            logger.exception(e)
    except* commands.errors.ExtensionFailed as eg:
        for e in eg.exceptions:
            logger.exception(e)
    logger.info("Finished loading cogs.")


async def unload_all_cogs(bot: Bot) -> None:
    """Unload all cogs in the cogs directory. Subdirectories are also searched.

    Args:
        bot: Bot to unload cogs from.
    """
    try:
        async with asyncio.TaskGroup() as tg:
            for file in recursive_module_search(pathlib.Path(COG_PATH)):
                tg.create_task(bot.unload_extension(file))
                logger.info("Unloaded cog %s", file)
    except* commands.errors.ExtensionNotLoaded as eg:
        for e in eg.exceptions:
            logger.warning(e)
    except* commands.errors.ExtensionNotFound as eg:
        for e in eg.exceptions:
            logger.warning(e)
    except* commands.errors.NoEntryPointError as eg:
        for e in eg.exceptions:
            logger.exception(e)
    except* commands.errors.ExtensionFailed as eg:
        for e in eg.exceptions:
            logger.exception(e)
    logger.info("Finished unloading cogs.")


def recursive_module_search(
    path: pathlib.Path, *, exclude: list[str] | None = None
) -> Generator[str, None, None]:
    """Recursively search for python modules in a directory.

    Args:
        path: Path to search.
        exclude: List of files to exclude.

    Returns:
        Generator yielding module paths as strings.
    """
    if exclude is None:
        exclude = []

    for f in path.rglob("*.py"):
        if f.is_file() and f.stem not in exclude:
            yield ".".join(f.parts[:-1] + (f.stem,))
