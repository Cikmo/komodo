from piccolo.apps.migrations.auto.migration_manager import MigrationManager


ID = "2024-08-31T19:09:25:553839"
VERSION = "1.17.0"
DESCRIPTION = ""


async def forwards():
    manager = MigrationManager(
        migration_id=ID, app_name="komodo", description=DESCRIPTION
    )

    manager.drop_column(
        table_class_name="Alliance",
        tablename="alliance",
        column_name="discord_link",
        db_column_name="discord_link",
        schema=None,
    )

    manager.drop_column(
        table_class_name="Alliance",
        tablename="alliance",
        column_name="forum_link",
        db_column_name="forum_link",
        schema=None,
    )

    manager.drop_column(
        table_class_name="Alliance",
        tablename="alliance",
        column_name="wiki_link",
        db_column_name="wiki_link",
        schema=None,
    )

    return manager
