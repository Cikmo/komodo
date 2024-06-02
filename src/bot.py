import asyncio
import logging
import os
import pathlib
import sys
from typing import Generator

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)

COG_PATH = "src/cogs"


class Bot(commands.Bot):

    async def setup_hook(self):

        await load_all_cogs(self)

    async def on_ready(self):
        assert self.user is not None
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")

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
            await self.load_extension(module)
            logger.info(f"Loaded cog {module}")
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
            await self.unload_extension(module)
            logger.info(f"Unloaded cog {module}")
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
            await self.reload_extension(module)
            logger.info(f"Reloaded cog {module}")
        except FileNotFoundError as e:
            raise commands.ExtensionNotFound(cog_name) from e

    async def shutdown(self, restart: bool = False):
        await self.close()
        logger.info("Closed bot.")

        if restart:
            os.execv(sys.executable, [sys.executable, *sys.argv])
        else:
            exit(0)


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
                logger.info(f"Loaded cog {file}")
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

    except* Exception as eg:
        for _ in eg.exceptions:
            logger.exception(f"Exception thrown while loading cog.")
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
                logger.info(f"Unloaded cog {file}")
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
    except* Exception as eg:
        for _ in eg.exceptions:
            logger.exception(f"Exception thrown while unloading cog.")
    logger.info("Finished unloading cogs.")


def recursive_module_search(
    path: pathlib.Path, *, exclude: list[str] = []
) -> Generator[str, None, None]:
    """Recursively search for python modules in a directory.

    Args:
        path: Path to search.
        exclude: List of files to exclude.

    Returns:
        Generator yielding module paths as strings.
    """
    for f in path.rglob("*.py"):
        if f.is_file() and f.stem not in exclude:
            yield ".".join(f.parts[:-1] + (f.stem,))
