from piccolo.apps.migrations.auto.migration_manager import MigrationManager


ID = "2024-09-08T21:15:31:484039"
VERSION = "1.17.0"
DESCRIPTION = ""


async def forwards():
    manager = MigrationManager(
        migration_id=ID, app_name="komodo", description=DESCRIPTION
    )

    manager.drop_column(
        table_class_name="Nation",
        tablename="nation",
        column_name="defensive_war_count",
        db_column_name="defensive_war_count",
        schema=None,
    )

    manager.drop_column(
        table_class_name="Nation",
        tablename="nation",
        column_name="offensive_war_count",
        db_column_name="offensive_war_count",
        schema=None,
    )

    return manager
