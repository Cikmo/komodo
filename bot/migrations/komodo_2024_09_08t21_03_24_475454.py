from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.columns.column_types import BigInt
from piccolo.columns.column_types import Real
from piccolo.columns.column_types import Timestamptz
from piccolo.columns.defaults.timestamptz import TimestamptzNow


ID = "2024-09-08T21:03:24:475454"
VERSION = "1.17.0"
DESCRIPTION = ""


async def forwards():
    manager = MigrationManager(
        migration_id=ID, app_name="komodo", description=DESCRIPTION
    )

    manager.alter_column(
        table_class_name="Nation",
        tablename="nation",
        column_name="update_timezone",
        db_column_name="update_timezone",
        params={"default": None},
        old_params={"default": 0.0},
        column_class=Real,
        old_column_class=Real,
        schema=None,
    )

    manager.alter_column(
        table_class_name="Nation",
        tablename="nation",
        column_name="last_active",
        db_column_name="last_active",
        params={"default": None, "null": True},
        old_params={"default": TimestamptzNow(), "null": False},
        column_class=Timestamptz,
        old_column_class=Timestamptz,
        schema=None,
    )

    manager.alter_column(
        table_class_name="Nation",
        tablename="nation",
        column_name="discord_id",
        db_column_name="discord_id",
        params={"default": None},
        old_params={"default": 0},
        column_class=BigInt,
        old_column_class=BigInt,
        schema=None,
    )

    manager.alter_column(
        table_class_name="Nation",
        tablename="nation",
        column_name="alliance_join_date",
        db_column_name="alliance_join_date",
        params={"default": None},
        old_params={"default": TimestamptzNow()},
        column_class=Timestamptz,
        old_column_class=Timestamptz,
        schema=None,
    )

    return manager
