"""This module contains functions to sync data from the API to the database."""

from src.bot import Bot
from src.database.tables.pnw import Nation


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
        result = (await bot.api_v3.get_nations(page=page, page_size=500)).nations

        if not result.paginator_info.has_more_pages:
            break

        nations = Nation.from_api_v3(result.data)

        inserted = await Nation.insert(
            *nations,
        ).on_conflict("id", "DO UPDATE")

        total_inserted += len(inserted)

        page += 1

    return total_inserted
