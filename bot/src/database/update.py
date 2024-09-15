import logging
import timeit
from itertools import batched

from src.database.tables.pnw import Alliance, Nation
from src.pnw.pnwapi import PnwAPI
from src.pnw.subscriptions.subscription import SubscriptionModel

logger = logging.getLogger(__name__)


async def update_all_nations(pnw_api: PnwAPI):
    start_time = timeit.default_timer()

    nations = await pnw_api.subscriptions.fetch_subscriptions_snapshot(
        SubscriptionModel.NATION
    )

    if not nations:
        return

    num_inserted = 0

    # The API may be bugged, and not completely removed all references to an alliance
    # when it is deleted. This means that there may be nations with alliance IDs that
    # no longer exist. We will check for this and set the alliance ID to 0 if it does
    # not exist.
    alliance_ids_found_in_nations = {
        nation.alliance for nation in nations if nation.alliance
    }

    existing_alliance_ids: list[int] = (
        await Alliance.select(Alliance.id)
        .where(Alliance.id.is_in(alliance_ids_found_in_nations))  # type: ignore
        .output(as_list=True)
    )

    invalid_alliance_ids = alliance_ids_found_in_nations - set(existing_alliance_ids)

    if invalid_alliance_ids:
        logger.warning(
            "Invalid alliance IDs found: %s. These will be set to 0.",
            invalid_alliance_ids,
        )

    # handle invalid alliance IDs
    for nation in nations:
        if nation.alliance in invalid_alliance_ids:
            nation.alliance = None

    # Get the IDs of nations returned by the API
    api_nation_ids = {nation.id for nation in nations}

    db = Nation._meta.db  # type: ignore # pylint: disable=protected-access

    async with db.transaction():
        for batch in batched(nations, 500):
            inserted = await Nation.insert(
                *[Nation(**nation.model_dump()) for nation in batch],
            ).on_conflict(
                Nation.id, "DO UPDATE", Nation.all_columns(exclude=[Nation.id])
            )
            num_inserted += len(inserted)

        # Get the IDs of nations currently in the database
        existing_nation_ids: list[int] = await Nation.select(Nation.id).output(
            as_list=True
        )

        # Find nation IDs to delete (present in DB but not in API response)
        nation_ids_to_delete = set(existing_nation_ids) - api_nation_ids

        if nation_ids_to_delete:
            logger.info(
                "Deleting %d nations not found in API response",
                len(nation_ids_to_delete),
            )
            # Delete nations that are no longer present in the API response
            await Nation.delete().where(Nation.id.is_in(nation_ids_to_delete))  # type: ignore

    end_time = timeit.default_timer()

    logger.info("Synced %s nations in %s seconds", num_inserted, end_time - start_time)


async def update_all_accounts(pnw_api: PnwAPI):
    start_time = timeit.default_timer()

    accounts = await pnw_api.subscriptions.fetch_subscriptions_snapshot(
        SubscriptionModel.ACCOUNT
    )

    if not accounts:
        return

    num_updated = 0

    # Accounts are not immediately deleted from the database when they are deleted.
    # Because of this, we need to check if the nation ID exists in the database before
    # inserting the account data.
    nation_ids: list[int] = await Nation.select(Nation.id).output(as_list=True)

    db = Nation._meta.db  # type: ignore # pylint: disable=protected-access

    async with db.transaction():
        for batch in batched(accounts, 500):
            updated = await Nation.insert(
                *[
                    Nation(**account.model_dump())
                    for account in batch
                    if account.id in nation_ids
                ],
            ).on_conflict(
                Nation.id, "DO UPDATE", [Nation.discord_id, Nation.last_active]
            )

            num_updated += len(updated)

    end_time = timeit.default_timer()

    logger.info("Synced %s accounts in %s seconds", num_updated, end_time - start_time)


async def update_all_alliances(pnw_api: PnwAPI):
    start_time = timeit.default_timer()

    alliances = await pnw_api.subscriptions.fetch_subscriptions_snapshot(
        SubscriptionModel.ALLIANCE
    )

    if not alliances:
        return

    num_inserted = 0

    db = Alliance._meta.db  # type: ignore # pylint: disable=protected-access

    async with db.transaction():
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
