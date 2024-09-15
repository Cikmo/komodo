"""
Handles PnW subscriptions
"""

import asyncio
from logging import getLogger
from typing import Any

from discord.ext import commands
from src.bot import Bot
from src.database.tables.pnw import Alliance, AlliancePosition, City, Nation
from src.database.update import (
    update_all_accounts,
    update_all_alliance_positions,
    update_all_alliances,
    update_all_cities,
    update_all_nations,
)
from src.pnw.api_v3 import (
    SubscriptionAccountFields,
    SubscriptionAllianceFields,
    SubscriptionAlliancePositionFields,
    SubscriptionCityFields,
    SubscriptionNationFields,
)
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

        self.models_to_subscribe_to: dict[
            SubscriptionModel, list[SubscriptionEvent]
        ] = {
            SubscriptionModel.NATION: SubscriptionEvent.all(),
            SubscriptionModel.ACCOUNT: [SubscriptionEvent.UPDATE],
            SubscriptionModel.ALLIANCE: SubscriptionEvent.all(),
            SubscriptionModel.ALLIANCE_POSITION: SubscriptionEvent.all(),
            SubscriptionModel.CITY: SubscriptionEvent.all(),
        }

    @commands.Cog.listener()
    async def on_ready(self):
        """Called when the bot is ready."""

        # TODO: Move these into a separate function,
        # which we call as a task. Inside of the update functions,
        # make it so that it will wait and retry if the rate limit is hit.
        await update_all_alliances(self.bot.pnw)
        await update_all_alliance_positions(self.bot.pnw)
        await update_all_nations(self.bot.pnw)
        await update_all_accounts(self.bot.pnw)

        # wait with updating cities because of the rate limit
        # but continue with the rest of the bot
        async def update_cities():
            await asyncio.sleep(60)
            await update_all_cities(self.bot.pnw)

        asyncio.create_task(update_cities())

        await self.initialize_subscriptions()

    async def initialize_subscriptions(self):
        """Subscribes to all events for the models specified in `models_to_subscribe_to`."""
        tasks: list[asyncio.Task[Any]] = []

        for model, allowed_events in self.models_to_subscribe_to.items():
            for event in allowed_events:
                method_name = f"on_{model}_{event}"
                method = getattr(self, method_name, None)

                if method is None:
                    logger.warning(
                        "Method %s not found in Subscriptions cog", method_name
                    )
                    continue

                # await self.bot.pnw.subscriptions.subscribe(
                #     model=model, event=event, callbacks=[method]
                # )
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

    async def on_nation_update(self, data: SubscriptionNationFields):
        """Called when a nation is updated."""

        # check if alliance exists in db
        if data.alliance:
            alliance_in_db = (
                await Alliance.select(Alliance.id)
                .where(Alliance.id == data.alliance)
                .first()
            )

            if not alliance_in_db:
                alliance_list = (
                    await self.bot.pnw.v3.get_subscription_alliance(data.alliance)
                ).alliances

                # get first element of data if alliance_list exists and alliance_list.data is not an empty list
                if alliance_list and alliance_list.data:
                    alliance_data = alliance_list.data[0]
                    await self.on_alliance_create(alliance_data)
                else:
                    logger.error(
                        "Alliance %s not found in database or API", data.alliance
                    )
                    data.alliance = None

        nation_in_db = await Nation.objects().where(Nation.id == data.id).first()

        if not nation_in_db:
            await self.on_nation_create(data)
            return

        # find the differences between the two nations
        nation_in_db_fields = nation_in_db.to_dict()
        nation_update_fields = data.model_dump()

        differences = {
            k: v
            for k, v in nation_update_fields.items()
            if nation_in_db_fields.get(k) != v
        }

        if not differences:
            return

        # update nation
        await Nation.update(**differences).where(Nation.id == data.id)

        for field, value in differences.items():
            logger.info(
                "Nation %s | %s updated: %s -> %s",
                data.id,
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
        existing_nation = (
            await Nation.select(Nation.id).where(Nation.id == data.id).first()
        )

        if existing_nation:
            return

        nation = Nation(**data.model_dump())

        try:
            await nation.save()
            logger.info("Nation created: %s", nation.id)
        except Exception as e:  # pylint: disable=broad-except
            logger.error("Error saving nation: %s", e)
            return

    async def on_nation_delete(self, data: SubscriptionNationFields):
        """Called when a nation is deleted."""
        deleted = await Nation.delete().where(Nation.id == data.id).returning(Nation.id)
        if deleted:
            logger.info("Nation deleted: %s", data.id)

    async def on_account_update(self, data: SubscriptionAccountFields):
        """Called when an account is updated."""
        # this will add info to a nation. Try a few times to get the nation, with a second between each try.
        # if no nation is found after 5 tries, give up

        nation = await Nation.objects().where(Nation.id == data.id).first()

        if not nation:
            return

        old_discord_id = nation.discord_id
        new_discord_id = data.discord_id

        nation.last_active = data.last_active
        nation.discord_id = new_discord_id

        await nation.save()

        if old_discord_id != new_discord_id:
            logger.info(
                "Account %s updated: discord_id %s -> %s",
                data.id,
                old_discord_id,
                new_discord_id,
            )
            self.bot.dispatch(
                "account_discord_id_update",
                nation,
                old_discord_id,
                new_discord_id,
            )

    async def on_alliance_create(self, data: SubscriptionAllianceFields):
        """Called when an alliance is created."""
        existing_alliance = (
            await Alliance.select(Alliance.id).where(Alliance.id == data.id).first()
        )

        if existing_alliance:
            return

        alliance = Alliance(**data.model_dump())

        try:
            await alliance.save()
            logger.info("Alliance created: %s", alliance.id)
        except Exception as e:  # pylint: disable=broad-except
            logger.error("Error saving alliance: %s", e)
            return

    async def on_alliance_update(self, data: SubscriptionAllianceFields):
        """Called when an alliance is updated."""

        alliance_in_db = await Alliance.objects().where(Alliance.id == data.id).first()

        if not alliance_in_db:
            await self.on_alliance_create(data)
            return

        # find the differences between the two alliances
        alliance_in_db_fields = alliance_in_db.to_dict()
        alliance_update_fields = data.model_dump()

        differences = {
            k: v
            for k, v in alliance_update_fields.items()
            if alliance_in_db_fields.get(k) != v
        }

        if not differences:
            return

        await Alliance.update(**differences).where(Alliance.id == data.id)

        for field, value in differences.items():
            logger.info(
                "Alliance %s | %s updated: %s -> %s",
                data.id,
                field,
                alliance_in_db_fields.get(field),
                value,
            )
            self.bot.dispatch(
                f"alliance_{field}_update",
                alliance_in_db,
            )

    async def on_alliance_delete(self, data: SubscriptionAllianceFields):
        """Called when an alliance is deleted."""
        deleted = (
            await Alliance.delete().where(Alliance.id == data.id).returning(Alliance.id)
        )
        if deleted:
            logger.info("Alliance deleted: %s", data.id)

    async def on_alliance_position_update(
        self, data: SubscriptionAlliancePositionFields
    ):
        """Called when an alliance position is updated."""
        alliance_position = (
            await AlliancePosition.objects()
            .where(AlliancePosition.id == data.id)
            .first()
        )

        if not alliance_position:
            return

        alliance_in_db = (
            await Alliance.select(Alliance.id)
            .where(Alliance.id == data.alliance)
            .first()
        )

        if not alliance_in_db:
            logger.warning(
                "Ignoring alliance position %s with invalid alliance %s",
                data.id,
                data.alliance,
            )

        alliance_position_in_db_fields = alliance_position.to_dict()
        alliance_update_fields = data.model_dump()

        differences = {
            k: v
            for k, v in alliance_update_fields.items()
            if alliance_position_in_db_fields.get(k) != v
        }

        if not differences:
            return

        await AlliancePosition.update(**differences).where(
            AlliancePosition.id == data.id
        )

        for field, value in differences.items():
            logger.info(
                "AlliancePosition %s | %s updated: %s -> %s",
                data.id,
                field,
                alliance_position_in_db_fields.get(field),
                value,
            )
            self.bot.dispatch(
                f"alliance_position_{field}_update",
                alliance_position,
            )

    async def on_alliance_position_create(
        self, data: SubscriptionAlliancePositionFields
    ):
        """Called when an alliance position is created."""
        existing_alliance_position = (
            await AlliancePosition.select(AlliancePosition.id)
            .where(AlliancePosition.id == data.id)
            .first()
        )

        if existing_alliance_position:
            return

        alliance_position = AlliancePosition(**data.model_dump())

        try:
            await alliance_position.save()
            logger.info("AlliancePosition created: %s", alliance_position.id)
        except Exception as e:  # pylint: disable=broad-except
            logger.error("Error saving alliance position: %s", e)
            return

    async def on_alliance_position_delete(
        self, data: SubscriptionAlliancePositionFields
    ):
        """Called when an alliance position is deleted."""
        deleted = (
            await AlliancePosition.delete()
            .where(AlliancePosition.id == data.id)
            .returning(AlliancePosition.id)
        )
        if deleted:
            logger.info("AlliancePosition deleted: %s", data.id)

    async def on_city_update(self, data: SubscriptionCityFields):
        """Called when a city is updated."""
        city = await City.objects().where(City.id == data.id).first()

        if not city:
            return

        nation_in_db = await Nation.objects().where(Nation.id == data.nation).first()

        if not nation_in_db:
            logger.warning(
                "Ignoring city %s with invalid nation %s",
                data.id,
                data.nation,
            )
            return

        city_in_db_fields = city.to_dict()
        city_update_fields = data.model_dump()

        differences = {
            k: v for k, v in city_update_fields.items() if city_in_db_fields.get(k) != v
        }

        if not differences:
            return

        await City.update(**differences).where(City.id == data.id)

        for field, value in differences.items():
            logger.info(
                "City %s | %s updated: %s -> %s",
                data.id,
                field,
                city_in_db_fields.get(field),
                value,
            )
            self.bot.dispatch(
                f"city_{field}_update",
                city,
            )

    async def on_city_create(self, data: SubscriptionCityFields):
        """Called when a city is created."""
        existing_city = await City.select(City.id).where(City.id == data.id).first()

        if existing_city:
            return

        for n in range(5):
            nation_in_db = (
                await Nation.objects().where(Nation.id == data.nation).first()
            )

            if nation_in_db:
                break

            if n == 4:
                logger.warning("Nation %s not found in database or API", data.nation)
                return

            await asyncio.sleep(1 * n)

        city = City(**data.model_dump())

        try:
            await city.save()
            logger.info("City created: %s", city.id)
        except Exception as e:  # pylint: disable=broad-except
            logger.error("Error saving city: %s", e)
            return

    async def on_city_delete(self, data: SubscriptionCityFields):
        """Called when a city is deleted."""
        deleted = await City.delete().where(City.id == data.id).returning(City.id)
        if deleted:
            logger.info("City deleted: %s", data.id)


async def setup(bot: Bot):
    """Called as extension is loaded"""
    await bot.add_cog(Subscriptions(bot))
