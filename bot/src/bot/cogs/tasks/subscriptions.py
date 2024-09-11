"""
Handles PnW subscriptions
"""

import asyncio
from logging import getLogger
from typing import Any

from discord.ext import commands
from src.bot import Bot
from src.pnw.api_v3 import SubscriptionNationFields
from src.pnw.subscriptions.subscription import SubscriptionEvent, SubscriptionModel

logger = getLogger(__name__)


class Subscriptions(commands.Cog):
    """
    Handles PnW subscriptions

    Subscribes to all events for the models specified in `models_to_subscribe_to`.

    Callbacks are named in the format `on_{model}_{event}` where `model` is the model name and `event` is the event name.
    """

    def __init__(self, bot: Bot):
        self.bot = bot

        self.models_to_subscribe_to = [
            SubscriptionModel.NATION,
        ]

    @commands.Cog.listener()
    async def on_ready(self):
        """Called when the bot is ready."""
        await self.initialize_subscriptions()

    async def initialize_subscriptions(self):
        """Subscribes to all events for the models specified in `models_to_subscribe_to`."""
        tasks: list[asyncio.Task[Any]] = []

        for model in self.models_to_subscribe_to:
            for event in SubscriptionEvent:
                method_name = f"on_{model}_{event}"
                method = getattr(self, method_name, None)

                if method is None:
                    logger.warning(
                        "Method %s not found in Subscriptions cog", method_name
                    )
                    continue

                tasks.append(
                    asyncio.create_task(
                        self.bot.pnw.subscriptions.subscribe(
                            model=model, event=event, callbacks=[method]
                        )
                    )
                )

        await asyncio.gather(*tasks)

        logger.info("Subscribed to all events")

    ### Callbacks ###

    async def on_nation_create(self, data: SubscriptionNationFields):
        """Called when a nation is created."""
        logger.info("Nation created: %s", data.id)

    async def on_nation_update(self, data: SubscriptionNationFields):
        """Called when a nation is updated."""
        logger.info("Nation updated: %s", data.id)

    async def on_nation_delete(self, data: SubscriptionNationFields):
        """Called when a nation is deleted."""
        logger.info("Nation deleted: %s", data.id)


async def setup(bot: Bot):
    """Called as extension is loaded"""
    await bot.add_cog(Subscriptions(bot))
