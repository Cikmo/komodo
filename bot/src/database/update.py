"""
This module contains functions for updating the database with the latest data from the PnW API.
"""

import logging
from itertools import batched

from src.database.tables.pnw import Alliance, AlliancePosition, City, Nation
from src.pnw.pnwapi import PnwAPI
from src.pnw.subscriptions.subscription import SubscriptionModel
from src.utils import Timer

logger = logging.getLogger(__name__)


@Timer()
async def update_all_nations(pnw_api: PnwAPI):
    """Fetches all nations from the API and updates the database with the new data.
    Deletes nations that are no longer present in the API response.

    Args:
        pnw_api: An instance of the PnwAPI class.
    """

    nations = await pnw_api.subscriptions.fetch_subscriptions_snapshot(
        SubscriptionModel.NATION
    )

    if not nations:
        return

    #####
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

    #####

    fetched_nation_ids = {nation.id for nation in nations}

    db = Nation._meta.db  # type: ignore # pylint: disable=protected-access

    async with db.transaction():
        for batch in batched(nations, 500):
            await Nation.insert(
                *[Nation(**nation.model_dump()) for nation in batch],
            ).on_conflict(
                Nation.id, "DO UPDATE", Nation.all_columns(exclude=[Nation.id])
            )

        db_nation_ids: list[int] = await Nation.select(Nation.id).output(as_list=True)

        nation_ids_to_delete = set(db_nation_ids) - fetched_nation_ids

        if nation_ids_to_delete:
            logger.info(
                "Deleting %d nations not found in API response",
                len(nation_ids_to_delete),
            )
            await Nation.delete().where(Nation.id.is_in(nation_ids_to_delete))  # type: ignore


@Timer()
async def update_all_accounts(pnw_api: PnwAPI):
    """Updates the database with the latest nation account data from the API.

    Args:
        pnw_api: An instance of the PnwAPI class.
    """

    accounts = await pnw_api.subscriptions.fetch_subscriptions_snapshot(
        SubscriptionModel.ACCOUNT
    )

    if not accounts:
        return

    # Accounts are not immediately deleted from the database when they are deleted.
    # Because of this, we need to check if the nation ID exists in the database before
    # inserting the account data.
    nation_ids: list[int] = await Nation.select(Nation.id).output(as_list=True)

    db = Nation._meta.db  # type: ignore # pylint: disable=protected-access

    async with db.transaction():
        for batch in batched(accounts, 500):
            await Nation.insert(
                *[
                    Nation(**account.model_dump())
                    for account in batch
                    if account.id in nation_ids
                ],
            ).on_conflict(
                Nation.id, "DO UPDATE", [Nation.discord_id, Nation.last_active]
            )


@Timer()
async def update_all_alliances(pnw_api: PnwAPI):
    """Fetches all alliances from the API and updates the database with the new data.

    Args:
        pnw_api: An instance of the PnwAPI class.
    """

    alliances = await pnw_api.subscriptions.fetch_subscriptions_snapshot(
        SubscriptionModel.ALLIANCE
    )

    if not alliances:
        return

    fetched_alliance_ids = {alliance.id for alliance in alliances}

    db = Alliance._meta.db  # type: ignore # pylint: disable=protected-access

    async with db.transaction():
        for batch in batched(alliances, 100):
            await Alliance.insert(
                *[Alliance(**alliance.model_dump()) for alliance in batch],
            ).on_conflict(
                Alliance.id, "DO UPDATE", Alliance.all_columns(exclude=[Alliance.id])
            )

        db_alliance_ids: list[int] = await Alliance.select(Alliance.id).output(
            as_list=True
        )

        alliance_ids_to_delete = set(db_alliance_ids) - fetched_alliance_ids

        if alliance_ids_to_delete:
            logger.info(
                "Deleting %d alliances not found in API response",
                len(alliance_ids_to_delete),
            )
            await Alliance.delete().where(Alliance.id.is_in(alliance_ids_to_delete))  # type: ignore


@Timer()
async def update_all_alliance_positions(pnw_api: PnwAPI):
    """Fetches all alliance positions from the API and updates the database with the new data.

    Args:
        pnw_api: An instance of the PnwAPI class.
    """

    alliance_positions = await pnw_api.subscriptions.fetch_subscriptions_snapshot(
        SubscriptionModel.ALLIANCE_POSITION
    )

    if not alliance_positions:
        return

    #####
    # The API may be bugged, and not completely removed all positions when an
    # alliance is deleted. This means that there may be positions with alliance IDs that
    # no longer exist. We will check for this and remove these positions from the list.
    alliance_ids_found_in_positions = {
        position.alliance for position in alliance_positions if position.alliance
    }

    existing_alliance_ids: list[int] = (
        await Alliance.select(Alliance.id)
        .where(Alliance.id.is_in(alliance_ids_found_in_positions))  # type: ignore
        .output(as_list=True)
    )

    invalid_alliance_ids = alliance_ids_found_in_positions - set(existing_alliance_ids)

    if invalid_alliance_ids:
        logger.warning(
            "Found %s invalid alliance IDs found in alliance positions. Will ignore these.",
            len(invalid_alliance_ids),
        )

    # remove positions with invalid alliance IDs
    alliance_positions = [
        position
        for position in alliance_positions
        if position.alliance not in invalid_alliance_ids
    ]

    #####

    fetched_alliance_position_ids = {position.id for position in alliance_positions}

    db = AlliancePosition._meta.db  # type: ignore # pylint: disable=protected-access

    async with db.transaction():
        for batch in batched(alliance_positions, 100):
            await AlliancePosition.insert(
                *[AlliancePosition(**position.model_dump()) for position in batch],
            ).on_conflict(
                AlliancePosition.id,
                "DO UPDATE",
                AlliancePosition.all_columns(exclude=[AlliancePosition.id]),
            )

        db_alliance_position_ids: list[int] = await AlliancePosition.select(
            AlliancePosition.id
        ).output(as_list=True)

        alliance_position_ids_to_delete = (
            set(db_alliance_position_ids) - fetched_alliance_position_ids
        )

        if alliance_position_ids_to_delete:
            logger.info(
                "Deleting %d alliance positions not found in API response",
                len(alliance_position_ids_to_delete),
            )
            await AlliancePosition.delete().where(
                AlliancePosition.id.is_in(alliance_position_ids_to_delete)  # type: ignore
            )


@Timer()
async def update_all_cities(pnw_api: PnwAPI):
    """Fetches all cities from the API and updates the database with the new data.

    Args:
        pnw_api: An instance of the PnwAPI class.
    """

    cities = await pnw_api.subscriptions.fetch_subscriptions_snapshot(
        SubscriptionModel.CITY
    )

    if not cities:
        return

    #####
    # The API may be bugged, and not have deleted a city when a nation is deleted.
    # This means that there may be cities with nation IDs that no longer exist.
    # We will check for this and remove these cities from the list.
    nation_ids_found_in_cities = {city.nation for city in cities}

    existing_nation_ids: list[int] = (
        await Nation.select(Nation.id)
        .where(Nation.id.is_in(nation_ids_found_in_cities))  # type: ignore
        .output(as_list=True)
    )

    invalid_nation_ids = nation_ids_found_in_cities - set(existing_nation_ids)

    if invalid_nation_ids:
        logger.warning(
            "Found %s invalid nation IDs found in cities. Will ignore these.",
            len(invalid_nation_ids),
        )

    # remove cities with invalid nation IDs
    cities = [city for city in cities if city.nation not in invalid_nation_ids]

    #####

    fetched_city_ids = {city.id for city in cities}

    db = City._meta.db  # type: ignore # pylint: disable=protected-access

    async with db.transaction():
        for batch in batched(cities, 500):
            await City.insert(
                *[City(**city.model_dump()) for city in batch],
            ).on_conflict(City.id, "DO UPDATE", City.all_columns(exclude=[City.id]))

        db_city_ids: list[int] = await City.select(City.id).output(as_list=True)

        city_ids_to_delete = set(db_city_ids) - fetched_city_ids

        if city_ids_to_delete:
            logger.info(
                "Deleting %d cities not found in API response",
                len(city_ids_to_delete),
            )
            await City.delete().where(City.id.is_in(city_ids_to_delete))  # type: ignore
