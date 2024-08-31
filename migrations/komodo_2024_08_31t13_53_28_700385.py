from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.columns.column_types import Integer
from piccolo.columns.column_types import Real


ID = "2024-08-31T13:53:28:700385"
VERSION = "1.17.0"
DESCRIPTION = ""


async def forwards():
    manager = MigrationManager(
        migration_id=ID, app_name="komodo", description=DESCRIPTION
    )

    manager.alter_column(
        table_class_name="City",
        tablename="city",
        column_name="land",
        db_column_name="land",
        params={},
        old_params={},
        column_class=Real,
        old_column_class=Integer,
        schema=None,
    )

    return manager
