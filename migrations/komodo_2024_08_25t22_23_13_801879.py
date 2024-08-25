from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.columns.column_types import BigInt
from piccolo.columns.column_types import Integer


ID = "2024-08-25T22:23:13:801879"
VERSION = "1.16.0"
DESCRIPTION = ""


async def forwards():
    manager = MigrationManager(
        migration_id=ID, app_name="komodo", description=DESCRIPTION
    )

    manager.alter_column(
        table_class_name="Nation",
        tablename="nation",
        column_name="project_bits",
        db_column_name="project_bits",
        params={},
        old_params={},
        column_class=BigInt,
        old_column_class=Integer,
        schema=None,
    )

    return manager
