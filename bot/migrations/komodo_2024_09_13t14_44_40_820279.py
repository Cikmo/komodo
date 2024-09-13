from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.columns.column_types import DoublePrecision
from piccolo.columns.column_types import Real


ID = "2024-09-13T14:44:40:820279"
VERSION = "1.17.0"
DESCRIPTION = ""


async def forwards():
    manager = MigrationManager(
        migration_id=ID, app_name="komodo", description=DESCRIPTION
    )

    manager.alter_column(
        table_class_name="Nation",
        tablename="nation",
        column_name="score",
        db_column_name="score",
        params={},
        old_params={},
        column_class=DoublePrecision,
        old_column_class=Real,
        schema=None,
    )

    manager.alter_column(
        table_class_name="Nation",
        tablename="nation",
        column_name="update_timezone",
        db_column_name="update_timezone",
        params={},
        old_params={},
        column_class=DoublePrecision,
        old_column_class=Real,
        schema=None,
    )

    return manager
