from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.columns.column_types import Integer


ID = "2024-09-01T23:05:51:814680"
VERSION = "1.17.0"
DESCRIPTION = ""


async def forwards():
    manager = MigrationManager(
        migration_id=ID, app_name="komodo", description=DESCRIPTION
    )

    manager.alter_column(
        table_class_name="War",
        tablename="war",
        column_name="ground_control_id",
        db_column_name="ground_control_id",
        params={"null": True},
        old_params={"null": False},
        column_class=Integer,
        old_column_class=Integer,
        schema=None,
    )

    manager.alter_column(
        table_class_name="War",
        tablename="war",
        column_name="air_superiority_id",
        db_column_name="air_superiority_id",
        params={"null": True},
        old_params={"null": False},
        column_class=Integer,
        old_column_class=Integer,
        schema=None,
    )

    manager.alter_column(
        table_class_name="War",
        tablename="war",
        column_name="naval_blockade_id",
        db_column_name="naval_blockade_id",
        params={"null": True},
        old_params={"null": False},
        column_class=Integer,
        old_column_class=Integer,
        schema=None,
    )

    manager.alter_column(
        table_class_name="War",
        tablename="war",
        column_name="winner_id",
        db_column_name="winner_id",
        params={"null": True},
        old_params={"null": False},
        column_class=Integer,
        old_column_class=Integer,
        schema=None,
    )

    return manager
