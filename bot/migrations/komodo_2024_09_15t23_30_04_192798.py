from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.columns.column_types import Date
from piccolo.columns.column_types import Timestamptz
from piccolo.columns.defaults.date import DateNow
from piccolo.columns.defaults.timestamptz import TimestamptzNow


ID = "2024-09-15T23:30:04:192798"
VERSION = "1.17.1"
DESCRIPTION = ""


async def forwards():
    manager = MigrationManager(
        migration_id=ID, app_name="komodo", description=DESCRIPTION
    )

    manager.alter_column(
        table_class_name="City",
        tablename="city",
        column_name="date_created",
        db_column_name="date_created",
        params={"default": DateNow()},
        old_params={"default": TimestamptzNow()},
        column_class=Date,
        old_column_class=Timestamptz,
        schema=None,
    )

    return manager
