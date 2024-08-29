from __future__ import annotations

from functools import lru_cache
from logging import getLogger
from typing import Any, Awaitable, Callable

from piccolo.table import Table

from src.database.tables.pnw import PnwBaseTable
from src.pnw.paginator import Paginator

logger = getLogger(__name__)


async def update_pnw_table(
    table_class: type[PnwBaseTable[Any]],
    fetch_function: Callable[..., Awaitable[Any]],
    query_args: dict[str, Any] | None = None,
    page_size: int = 100,
    batch_size: int = 5,
) -> int:
    """
    Syncs data from the API to the database.

    Args:
        table_class: The database model class corresponding to the entity.
        fetch_function: The API function to fetch entities.
        query_args: Pass additional query arguments to the fetch function. If not provided, all entities are fetched.
        page_size: Number of entities to fetch per API call.
        batch_size: Number of pages to fetch in each batch.

    Returns:
        The number of rows inserted or updated.
    """
    query_args = query_args or {}

    async def insert_entities(entities: list[Any]) -> int:
        batch_models = [table_class.from_api_v3(entity) for entity in entities]
        inserted = await table_class.insert(*batch_models).on_conflict(  # type: ignore
            table_class.id,  # type: ignore
            "DO UPDATE",
            table_class.all_columns(exclude=[table_class.id]),  # type: ignore
        )
        return len(inserted)

    paginator = Paginator(
        fetch_function=fetch_function,
        page_size=page_size,
        batch_size=batch_size,
        **query_args,
    )

    db = table_class._meta.db  # type: ignore # pylint: disable=protected-access

    max_insert_batch_size = _get_max_batch_size(table_class)

    total_inserted = 0
    current_insert_batch: list[Any] = []
    async with db.transaction():
        async for entity in paginator:
            current_insert_batch.append(entity)

            if len(current_insert_batch) >= max_insert_batch_size:
                total_inserted += await insert_entities(current_insert_batch)
                current_insert_batch = []

        if current_insert_batch:
            total_inserted += await insert_entities(current_insert_batch)

    return total_inserted


@lru_cache
def _get_max_batch_size(table: type[Table]) -> int:
    """Calculates the maximum number of items that can be inserted in a single batch."""
    postgres_max_parameters = 32767

    assert issubclass(table, Table)
    return postgres_max_parameters // len(table.all_columns())
