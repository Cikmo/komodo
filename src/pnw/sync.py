"""This module contains functions to sync data from the API to the database."""

from logging import getLogger

from src.bot import Bot
from src.database.tables.pnw import Nation

logger = getLogger(__name__)

import asyncio
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional, TypeVar

T = TypeVar("T")


class Paginator:
    def __init__(
        self,
        fetch_function: Callable[..., Any],
        page_size: int = 100,
        batch_size: int = 5,
        **kwargs: Any
    ):
        """
        Initializes the paginator.

        Args:
            fetch_function: The function to fetch paginated data. Should return an object with
                            `data` and `paginator_info` attributes.
            page_size: The number of items per page.
            batch_size: The number of pages to fetch in each batch.
            **kwargs: Additional arguments to pass to the fetch function.
        """
        self.fetch_function = fetch_function
        self.page_size = page_size
        self.batch_size = batch_size
        self.kwargs = kwargs
        self.page = 1

    async def _fetch_page(self, page: int) -> Any:
        return await self.fetch_function(
            page=page, page_size=self.page_size, **self.kwargs
        )

    async def _fetch_batch(self) -> List[Any]:
        tasks = [self._fetch_page(self.page + i) for i in range(self.batch_size)]
        results = await asyncio.gather(*tasks)
        self.page += self.batch_size
        return results

    async def fetch_all(self) -> List[T]:
        """
        Fetches all items by paginating through all pages.

        Returns:
            A list of all fetched items.
        """
        all_items = []
        while True:
            results = await self._fetch_batch()
            for result in results:
                all_items.extend(result.nations.data)
                if not result.nations.paginator_info.has_more_pages:
                    return all_items

    async def __aiter__(self) -> AsyncGenerator[T, None]:
        """
        Supports asynchronous iteration with 'async for'.

        Yields:
            Items one by one as they are fetched.
        """
        while True:
            results = await self._fetch_batch()
            for result in results:
                for item in result.nations.data:
                    yield item
                if not result.nations.paginator_info.has_more_pages:
                    return


# Example usage of the Paginator class
async def sync_all_nations(bot: Bot) -> int:
    total_inserted = 0

    paginator = Paginator(
        fetch_function=bot.api_v3.get_nations, page_size=500, batch_size=10
    )

    all_columns_except_id = [
        column for column in Nation.all_columns() if column != "id"
    ]

    nations: list[list[Any]] = []

    async for nation_data, has_more_pages in paginator:
        print(nation_data)
        nations.append(Nation.from_api_v3(nation_data))

        if len(nations) >= 500:
            inserted = await Nation.insert(
                *nations,
            ).on_conflict(Nation.id, action="DO UPDATE", values=all_columns_except_id)
            total_inserted += len(inserted)
            logger.info("Inserted %s nations", len(inserted))
            nations = []
        elif not has_more_pages:
            inserted = await Nation.insert(
                *nations,
            ).on_conflict(Nation.id, action="DO UPDATE", values=all_columns_except_id)
            total_inserted += len(inserted)
            logger.info("Inserted %s nations", len(inserted))

    logger.info("Inserted %s nations", total_inserted)

    return total_inserted


# TODO: Create a custom version of async_base_client, where
# we add a rate limiter directly to the client, and also increase the rate limit from 5 seconds to like 30 seconds.

# TODO: Add a bulk query so multiple pages can be fetched at once. Will increase speed of syncing by a lot.


# async def sync_all_nations(bot: Bot) -> int:
#     """Sync all nations from the API to the database.

#     Args:
#         bot: The bot instance. Contains the API client.

#     Returns:
#         The number of nations inserted or updated.
#     """
#     total_inserted = 0

#     page = 1
#     while True:
#         result = (await bot.api_v3.get_nations(page=page, page_size=100)).nations

#         if not result.paginator_info.has_more_pages:
#             break

#         # we can get total pages from result.paginator_info.total_pages

#         nations = Nation.from_api_v3(result.data)

#         all_columns_except_id = [
#             column for column in Nation.all_columns() if column != "id"
#         ]

#         inserted = await Nation.insert(
#             *nations,
#         ).on_conflict(Nation.id, action="DO UPDATE", values=all_columns_except_id)

#         total_inserted += len(inserted)
#         logger.info("Inserted %s nations from page %s", len(inserted), page)

#         page += 1

#     return total_inserted
