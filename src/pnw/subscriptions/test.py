import asyncio
import logging
from typing import Any

import aiohttp

from src.config import get_settings
from src.pnw.subscriptions.asyncpusher.pusher import Pusher

logger = logging.getLogger(__name__)


async def handle_event(data: Any):
    logger.info(f"Received event...")


async def channel_authenticator(data: Any):
    # https://api.politicsandwar.com/subscriptions/v1/auth
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.politicsandwar.com/subscriptions/v1/auth", data=data
        ) as response:
            return await response.json()


async def get_channel(name: str, event: str) -> str | None:
    url = f"https://api.politicsandwar.com/subscriptions/v1/subscribe/{name}/{event}?api_key={get_settings().pnw.api_key}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            # try to get "channel" from response jason
            return (await response.json()).get("channel")


async def subscribe():
    loop = asyncio.get_running_loop()

    pusher = Pusher(
        "a22734a47847a64386c8",
        custom_host="socket.politicsandwar.com",
        channel_authenticator=channel_authenticator,
        loop=loop,
    )

    channel_name = await get_channel("nation", "update")

    if not channel_name:
        logger.error("Could not get channel name.")
        return

    await pusher.connect()
    channel = await pusher.subscribe(channel_name)
    channel.bind("BULK_NATION_UPDATE", handle_event)
    await asyncio.sleep(30)
    await pusher.unsubscribe(channel_name)
    await asyncio.sleep(1)
    await pusher.disconnect()
