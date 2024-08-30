"""This module contains functions to sync data from the API to the database."""

from __future__ import annotations

import asyncio
from logging import getLogger
from typing import (
    Any,
    AsyncGenerator,
    Awaitable,
    Callable,
    Generic,
    Protocol,
    TypeVar,
    overload,
)

from src.pnw.api_v3 import GetCities, GetNations
from src.pnw.api_v3.get_cities import GetCitiesCitiesData
from src.pnw.api_v3.get_nations import GetNationsNationsData

logger = getLogger(__name__)


T = TypeVar("T", bound=GetNations | GetCities)


class Paginator(Generic[T]):
    """Paginates through a list of items fetched from an API."""

    def __init__(
        self,
        fetch_function: Callable[..., Awaitable[T]],
        page_size: int = 100,
        batch_size: int = 5,
        **kwargs: Any,
    ) -> None:
        """
        Initializes the paginator.

        Args:
            fetch_function: The function to fetch paginated data. Should return an object with
                            `data` and `paginator_info` attributes.
            page_size: The number of items per page.
            batch_size: The number of pages to fetch in each batch.
            **kwargs: Additional arguments to pass to the fetch function.
        """
        if batch_size > 10:
            logger.warning(
                "It is not recommended to set the batch size greater than 10 due to rate limiting."
            )

        self.fetch_function = fetch_function
        self.page_size = page_size
        self.batch_size = batch_size
        self.page = 1

        self.kwargs: dict[str, Any] = kwargs

    async def _fetch_page(self, page: int) -> T:

        return await self.fetch_function(
            page=page, page_size=self.page_size, **self.kwargs
        )

    async def _fetch_batch(self) -> list[T]:
        tasks = [self._fetch_page(self.page + i) for i in range(self.batch_size)]
        results = await asyncio.gather(*tasks)
        self.page += self.batch_size
        return results

    @overload
    async def __aiter__(
        self: Paginator[GetNations],
    ) -> AsyncGenerator[GetNationsNationsData, None]: ...

    @overload
    async def __aiter__(
        self: Paginator[GetCities],
    ) -> AsyncGenerator[GetCitiesCitiesData, None]: ...

    async def __aiter__(
        self,
    ) -> AsyncGenerator[Any, None]:
        """
        Supports asynchronous iteration with 'async for'.

        Yields:
            Items one by one as they are fetched.
        """

        while True:
            results: list[T] = await self._fetch_batch()
            for result in results:
                first_attr_name: str = next(  # pylint: disable=stop-iteration-return
                    iter(result.__dict__)
                )
                first_attr_value: FirstItem = getattr(result, first_attr_name)

                for item in first_attr_value.data:
                    yield item

                if not result:
                    return

                if not first_attr_value.paginator_info.has_more_pages:
                    return


class PaginatorInfo(Protocol):
    """A protocol for objects with a has_more_pages attribute."""

    has_more_pages: bool


class FirstItem(Protocol):
    """A protocol for objects with a data attribute."""

    data: GetCitiesCitiesData | GetNationsNationsData
    paginator_info: PaginatorInfo
