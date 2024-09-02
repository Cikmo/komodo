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

from src.pnw.api_v3 import GetAlliances, GetCities, GetNations
from src.pnw.api_v3.get_alliances import GetAlliancesAlliancesData
from src.pnw.api_v3.get_cities import GetCitiesCitiesData
from src.pnw.api_v3.get_nations import GetNationsNationsData

logger = getLogger(__name__)


T = TypeVar("T", bound=GetNations | GetCities | GetAlliances)


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

    @overload
    async def __aiter__(
        self: Paginator[GetAlliances],
    ) -> AsyncGenerator[GetAlliancesAlliancesData, None]: ...

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

    async def batch(self, size: int = 50) -> AsyncGenerator[list[Any], None]:
        """A generator that yields batches of items.

        Args:
            size: The number of items per batch.

        Yields:
            A list of items with the specified size.
        """

        to_yield: list[Any] = []
        should_return: bool = False

        while True:
            results: list[T] = await self._fetch_batch()

            for result in results:
                first_attr_name: str = next(  # pylint: disable=stop-iteration-return
                    iter(result.__dict__)
                )
                first_attr_value: FirstItem = getattr(result, first_attr_name)

                # Add as much data as possible to to_yield without exceeding the target size,
                # then update data to remove the portion that was just added.
                data = first_attr_value.data
                while len(data) > 0:
                    remaining_space = size - len(to_yield)
                    to_yield.extend(data[:remaining_space])
                    data = data[remaining_space:]

                    if len(to_yield) == size:
                        yield to_yield
                        to_yield = []

                if not first_attr_value.paginator_info.has_more_pages:
                    should_return = True

            if should_return:
                if to_yield:
                    yield to_yield
                return


class PaginatorInfo(Protocol):
    """A protocol for objects with a has_more_pages attribute."""

    has_more_pages: bool


class FirstItem(Protocol):
    """A protocol for objects with a data attribute."""

    data: (
        list[GetCitiesCitiesData]
        | list[GetNationsNationsData]
        | list[GetAlliancesAlliancesData]
    )
    paginator_info: PaginatorInfo
