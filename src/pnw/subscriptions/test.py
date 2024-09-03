"""Testing subscriptions."""

import asyncio
import logging
from typing import Any

import aiohttp

from src.config import get_settings
from src.pnw.subscriptions.asyncpusher import Pusher

logger = logging.getLogger(__name__)


async def handle_nation(data: dict[str, Any]):
    """Handle event."""
    logger.info("Handling nation with id: %s", data["id"])


async def handle_bulk_nation(data: list[dict[str, Any]]):
    """Handle event."""

    for nation in data:
        await handle_nation(nation)


async def get_channel(name: str, event: str) -> str | None:
    """Get channel name."""
    url = (
        f"https://api.politicsandwar.com/subscriptions/v1/subscribe/{name}/{event}"
        f"?api_key={get_settings().pnw.api_key}"
    )

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            # try to get "channel" from response jason
            return (await response.json()).get("channel")


async def subscribe():
    """Subscribe to nation."""
    pusher = Pusher(
        "a22734a47847a64386c8",
        custom_host="socket.politicsandwar.com",
        auth_endpoint="https://api.politicsandwar.com/subscriptions/v1/auth",
    )

    channel_name = await get_channel("nation", "update")

    if not channel_name:
        logger.error("Could not get channel name.")
        return

    await pusher.connect()

    channel = await pusher.subscribe(channel_name)

    channel.bind("BULK_NATION_UPDATE", handle_bulk_nation)
    channel.bind("NATION_UPDATE", handle_nation)

    await asyncio.sleep(120)

    await pusher.unsubscribe(channel_name)

    await asyncio.sleep(1)

    await pusher.disconnect()
