"""
Handles PnW subscriptions
"""

import asyncio
from asyncio import Semaphore
from logging import getLogger
from typing import Any, cast

from discord.ext import commands
from src.bot import Bot
from src.database.tables.pnw import Nation
from src.pnw.api_v3 import SubscriptionNationFields
from src.pnw.subscriptions.subscription import SubscriptionEvent, SubscriptionModel

logger = getLogger(__name__)


class Subscriptions(commands.Cog):
    """
    Handles PnW subscriptions

    Subscribes to all events for the models specified in `models_to_subscribe_to`.

    Callbacks are named in the format `on_{model}_{event}` where `model` is the
    model name and `event` is the event name.
    """

    def __init__(self, bot: Bot):
        self.bot = bot

        self.models_to_subscribe_to = [
            SubscriptionModel.NATION,
        ]

        self.create_nation_semaphore = Semaphore(1)

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

                await self.bot.pnw.subscriptions.subscribe(
                    model=model, event=event, callbacks=[method]
                )

        logger.info("Subscribed to all events")

    ### Callbacks ###

    async def on_nation_update(self, data: SubscriptionNationFields):
        """Called when a nation is updated."""

        nation = cast(Nation, Nation.from_api_v3(data))  # type: ignore

        nation_in_db = await Nation.objects().where(Nation.id == nation.id).first()

        if not nation_in_db:
            # async with self.create_nation_semaphore:
            await self.on_nation_create(data)
            return

        # find the differences between the two nations
        nation_fields = nation.to_dict()
        nation_in_db_fields = nation_in_db.to_dict()

        differences = {
            k: v for k, v in nation_fields.items() if nation_in_db_fields.get(k) != v
        }

        if not differences:
            return

        nation._exists_in_db = True  # type: ignore # pylint: disable=protected-access
        await nation.save()

        for field, value in differences.items():
            logger.info(
                "Nation %s updated: %s -> %s",
                field,
                nation_in_db_fields.get(field),
                value,
            )
            self.bot.dispatch(
                f"nation_{field}_update",
                nation_in_db,
            )

    async def on_nation_create(self, data: SubscriptionNationFields):
        """Called when a nation is created."""
        nation = cast(Nation, Nation.from_api_v3(data))  # type: ignore

        nation_in_db = (
            await Nation.select(Nation.id).where(Nation.id == nation.id).first()
        )

        if nation_in_db:
            return

        try:
            await nation.save()
            logger.info("Nation created: %s", nation.id)
        except Exception as e:  # pylint: disable=broad-except
            logger.error("Error saving nation: %s", e)
            return

    async def on_nation_delete(self, data: SubscriptionNationFields):
        """Called when a nation is deleted."""
        logger.info("Nation deleted: %s", data.id)


async def setup(bot: Bot):
    """Called as extension is loaded"""
    await bot.add_cog(Subscriptions(bot))
