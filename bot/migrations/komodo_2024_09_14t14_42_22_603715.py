from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.columns.column_types import DoublePrecision
from piccolo.columns.column_types import Real


ID = "2024-09-14T14:42:22:603715"
VERSION = "1.17.0"
DESCRIPTION = ""


async def forwards():
    manager = MigrationManager(
        migration_id=ID, app_name="komodo", description=DESCRIPTION
    )

    manager.drop_column(
        table_class_name="Alliance",
        tablename="alliance",
        column_name="average_score",
        db_column_name="average_score",
        schema=None,
    )

    manager.drop_column(
        table_class_name="Alliance",
        tablename="alliance",
        column_name="rank",
        db_column_name="rank",
        schema=None,
    )

    manager.alter_column(
        table_class_name="Alliance",
        tablename="alliance",
        column_name="score",
        db_column_name="score",
        params={},
        old_params={},
        column_class=DoublePrecision,
        old_column_class=Real,
        schema=None,
    )

    return manager
