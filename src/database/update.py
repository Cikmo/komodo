"""
This module contains functions to update database rows with data fetched from the Politics and War API.
"""

from __future__ import annotations

from functools import lru_cache
from logging import getLogger
from typing import Any, Awaitable, Callable, Literal, overload

from piccolo.table import Table

from src.database.tables.pnw import Alliance, City, Nation, PnwBaseTable
from src.pnw.api_v3 import Client
from src.pnw.paginator import Paginator

logger = getLogger(__name__)


async def update_all_nations(client: Client) -> tuple[int, int]:
    """
    Updates the nations table with data fetched from the Politics and War API.

    Returns:
        A tuple containing the number of nations and cities inserted or updated.
    """

    nations_inserted = await update_pnw_table(
        Nation,
        client.get_nations,
        page_size=500,
        batch_size=10,
    )

    cities_inserted = await update_pnw_table(
        City,
        client.get_cities,
        page_size=500,
        batch_size=10,
    )

    return nations_inserted, cities_inserted


async def update_alliances(client: Client) -> int:
    """
    Updates the alliances table with data fetched from the Politics and War API.

    Returns:
        The number of alliances inserted or updated.
    """
    return await update_pnw_table(
        Alliance, client.get_alliances, page_size=500, batch_size=2
    )


async def update_all_tables(client: Client) -> tuple[int, int, int]:
    """
    Updates all tables with data fetched from the Politics and War API.

    Returns:
        A tuple containing the number of alliances, nations and cities inserted or updated.
    """
    alliances_inserted = await update_alliances(client)
    nations_inserted, cities_inserted = await update_all_nations(client)
    return alliances_inserted, nations_inserted, cities_inserted


@overload
async def update_pnw_table(
    table_class: type[PnwBaseTable[Any]],
    fetch_function: Callable[..., Awaitable[Any]],
    query_args: dict[str, Any] | None = None,
    page_size: int = 100,
    batch_size: int = 5,
    return_ids: Literal[False] = False,
) -> int: ...


@overload
async def update_pnw_table(
    table_class: type[PnwBaseTable[Any]],
    fetch_function: Callable[..., Awaitable[Any]],
    query_args: dict[str, Any] | None = None,
    page_size: int = 100,
    batch_size: int = 5,
    return_ids: Literal[True] = True,
) -> set[int]: ...


async def update_pnw_table(
    table_class: type[PnwBaseTable[Any]],
    fetch_function: Callable[..., Awaitable[Any]],
    query_args: dict[str, Any] | None = None,
    page_size: int = 100,
    batch_size: int = 5,
    return_ids: bool = False,
) -> int | set[int]:
    """
    Updates database rows with data fetched from the Politics and War API.

    Args:
        table_class: The database model class corresponding to the entity.
        fetch_function: The API function to fetch entities.
        query_args: Pass additional query arguments to the fetch function. If not provided, all entities are fetched.
        page_size: Number of entities to fetch per API call.
        batch_size: Number of pages to fetch in each batch.
        return_ids: If True, returns a set of IDs of the entities inserted or updated.

    Returns:
        The number of rows inserted or updated if return_ids is False, otherwise
        a set of IDs of the entities inserted or updated.
    """
    logger.info("Updating %s table...", table_class.__name__)

    query_args = query_args or {}
    paginator = Paginator(
        fetch_function=fetch_function,
        page_size=page_size,
        batch_size=batch_size,
        **query_args,
    )

    max_insert_batch_size = _get_max_batch_size(table_class)

    total_inserted = 0
    current_insert_batch: list[Any] = []
    returned_ids: set[int] = set()

    existing_ids = await _get_existing_ids(table_class, query_args)

    async for entity in paginator:
        current_insert_batch.append(entity)
        returned_ids.add(int(entity.id))

        if len(current_insert_batch) >= max_insert_batch_size:
            total_inserted += await _insert_entities(current_insert_batch, table_class)
            current_insert_batch = []

    print(current_insert_batch)

    if current_insert_batch:
        total_inserted += await _insert_entities(current_insert_batch, table_class)

    if not query_args:
        await _delete_stale_ids(existing_ids, returned_ids, table_class)

    logger.info("Updated %s rows to %s", total_inserted, table_class.__name__)
    return total_inserted if not return_ids else returned_ids


async def _insert_entities(
    entities: list[Any], table_class: type[PnwBaseTable[Any]]
) -> int:
    """
    Inserts or updates entities in the database.

    Args:
        entities: The list of entities to insert or update.
        table_class: The database model class corresponding to the entity.

    Returns:
        The number of rows inserted or updated.
    """

    batch_models = [table_class.from_api_v3(entity) for entity in entities]

    inserted = await table_class.insert(*batch_models).on_conflict(  # type: ignore
        table_class.id,  # type: ignore
        "DO UPDATE",
        table_class.all_columns(exclude=[table_class.id]),  # type: ignore
    )
    return len(inserted)


async def _get_existing_ids(
    table_class: type[PnwBaseTable[Any]],
    query_args: dict[str, Any],
) -> set[int]:
    """
    Retrieves existing IDs from the database.

    Args:
        table_class: The database model class corresponding to the entity.
        query_args: Query arguments passed to the fetch function.

    Returns:
        A set of existing IDs in the database.
    """
    if not query_args:
        return set(
            await table_class.select(table_class.id).output(as_list=True)  # type: ignore
        )
    return set()


async def _delete_stale_ids(
    existing_ids: set[int],
    returned_ids: set[int],
    table_class: type[PnwBaseTable[Any]],
) -> None:
    """
    Deletes stale IDs that are no longer present in the API response.

    Args:
        existing_ids: The set of existing IDs in the database.
        returned_ids: The set of IDs returned by the API.
        table_class: The database model class corresponding to the entity.
    """
    ids_to_delete = existing_ids - returned_ids
    if ids_to_delete:
        logger.info(
            "Deleting %s rows from %s that are not in the API response",
            len(ids_to_delete),
            table_class.__name__,
        )
        await table_class.delete().where(table_class.id.is_in(ids_to_delete))  # type: ignore


@lru_cache
def _get_max_batch_size(table: type[Table]) -> int:
    """Calculates the maximum number of items that can be inserted in a single batch."""
    # Special case for alliances since it likes to act dumb
    if table is Alliance:
        return 500

    postgres_max_parameters = 32767

    assert issubclass(table, Table)
    return postgres_max_parameters // len(table.all_columns())
