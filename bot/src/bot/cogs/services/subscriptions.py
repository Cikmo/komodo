"""
Handles PnW subscriptions
"""

import timeit
from itertools import batched
from logging import getLogger

from asyncpg import ForeignKeyViolationError  # type: ignore

from discord.ext import commands
from src.bot import Bot
from src.database.tables.pnw import Alliance, Nation
from src.pnw.api_v3 import (
    SubscriptionAccountFields,
    SubscriptionAllianceFields,
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
        }

    @commands.Cog.listener()
    async def on_ready(self):
        """Called when the bot is ready."""

        await self.sync_all_alliances()
        await self.sync_all_nations()
        await self.sync_all_accounts()

        await self.initialize_subscriptions()

    async def sync_all_nations(self):
        start_time = timeit.default_timer()

        nations = await self.bot.pnw.subscriptions.fetch_subscriptions_snapshot(
            SubscriptionModel.NATION
        )

        num_inserted = 0

        for batch in batched(nations, 500):
            inserted = []

            try:
                inserted = await Nation.insert(
                    *[Nation(**nation.model_dump()) for nation in batch],
                ).on_conflict(
                    Nation.id, "DO UPDATE", Nation.all_columns(exclude=[Nation.id])
                )
            except ForeignKeyViolationError:
                # insert 10 at a time
                for batch_10 in batched(batch, 50):
                    try:
                        inserted = await Nation.insert(
                            *[Nation(**nation.model_dump()) for nation in batch_10],
                        ).on_conflict(
                            Nation.id,
                            "DO UPDATE",
                            Nation.all_columns(exclude=[Nation.id]),
                        )

                        num_inserted += len(inserted)
                    except ForeignKeyViolationError:
                        # insert 1 at a time
                        for nation in batch_10:
                            try:
                                inserted = await Nation.insert(
                                    Nation(**nation.model_dump())
                                ).on_conflict(
                                    Nation.id,
                                    "DO UPDATE",
                                    Nation.all_columns(exclude=[Nation.id]),
                                )
                                num_inserted += len(inserted)
                            except ForeignKeyViolationError:
                                logger.warning(
                                    "Nation %s has invalid alliance %s",
                                    nation.id,
                                    nation.alliance,
                                )

                                nation.alliance = 0
                                inserted = await Nation.insert(
                                    Nation(**nation.model_dump())
                                ).on_conflict(
                                    Nation.id,
                                    "DO UPDATE",
                                    Nation.all_columns(exclude=[Nation.id]),
                                )

            num_inserted += len(inserted)

        end_time = timeit.default_timer()

        logger.info(
            "Synced %s nations in %s seconds", num_inserted, end_time - start_time
        )

    async def sync_all_accounts(self):
        start_time = timeit.default_timer()

        accounts = await self.bot.pnw.subscriptions.fetch_subscriptions_snapshot(
            SubscriptionModel.ACCOUNT
        )

        num_updated = 0

        db = Nation._meta.db  # type: ignore # pylint: disable=protected-access

        async with db.transaction():
            for account in accounts:
                updated = (
                    await Nation.update(
                        discord_id=account.discord_id,
                        last_active=account.last_active,
                    )
                    .where(Nation.id == account.id)
                    .returning(Nation.id)
                )

                num_updated += len(updated)

        end_time = timeit.default_timer()

        logger.info(
            "Synced %s accounts in %s seconds", num_updated, end_time - start_time
        )

    async def sync_all_alliances(self):
        start_time = timeit.default_timer()

        alliances = await self.bot.pnw.subscriptions.fetch_subscriptions_snapshot(
            SubscriptionModel.ALLIANCE
        )

        num_inserted = 0

        for batch in batched(alliances, 100):
            inserted = await Alliance.insert(
                *[Alliance(**alliance.model_dump()) for alliance in batch],
            ).on_conflict(
                Alliance.id, "DO UPDATE", Alliance.all_columns(exclude=[Alliance.id])
            )

            num_inserted += len(inserted)

        end_time = timeit.default_timer()

        logger.info(
            "Synced %s alliances in %s seconds", num_inserted, end_time - start_time
        )

    async def initialize_subscriptions(self):
        """Subscribes to all events for the models specified in `models_to_subscribe_to`."""
        for model, allowed_events in self.models_to_subscribe_to.items():
            for event in allowed_events:
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


async def setup(bot: Bot):
    """Called as extension is loaded"""
    await bot.add_cog(Subscriptions(bot))
