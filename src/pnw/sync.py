"""This module contains functions to sync data from the API to the database."""

from logging import getLogger

from src.bot import Bot
from src.database.tables.pnw import Nation

logger = getLogger(__name__)

# TODO: Create a custom version of async_base_client, where
# we add a rate limiter directly to the client, and also increase the rate limit from 5 seconds to like 30 seconds.

# TODO: Add a bulk query so multiple pages can be fetched at once. Will increase speed of syncing by a lot.


async def sync_all_nations(bot: Bot) -> int:
    """Sync all nations from the API to the database.

    Args:
        bot: The bot instance. Contains the API client.

    Returns:
        The number of nations inserted or updated.
    """
    total_inserted = 0

    page = 1
    while True:
        result = (await bot.api_v3.get_nations(page=page, page_size=100)).nations

        if not result.paginator_info.has_more_pages:
            break

        nations = Nation.from_api_v3(result.data)

        all_columns_except_id = [
            column for column in Nation.all_columns() if column != "id"
        ]

        inserted = await Nation.insert(
            *nations,
        ).on_conflict(Nation.id, action="DO UPDATE", values=all_columns_except_id)

        total_inserted += len(inserted)
        logger.info("Inserted %s nations from page %s", len(inserted), page)

        page += 1

    return total_inserted
