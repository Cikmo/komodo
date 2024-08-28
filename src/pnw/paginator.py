"""This module contains functions to sync data from the API to the database."""

from logging import getLogger

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
