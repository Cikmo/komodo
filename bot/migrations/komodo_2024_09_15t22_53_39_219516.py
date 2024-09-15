from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.columns.column_types import Date
from piccolo.columns.column_types import Timestamptz
from piccolo.columns.defaults.timestamptz import TimestamptzNow


ID = "2024-09-15T22:53:39:219516"
VERSION = "1.17.1"
DESCRIPTION = ""


async def forwards():
    manager = MigrationManager(
        migration_id=ID, app_name="komodo", description=DESCRIPTION
    )

    manager.alter_column(
        table_class_name="City",
        tablename="city",
        column_name="last_nuke_in_game_date",
        db_column_name="last_nuke_in_game_date",
        params={"default": None},
        old_params={"default": TimestamptzNow()},
        column_class=Date,
        old_column_class=Timestamptz,
        schema=None,
    )

    return manager
