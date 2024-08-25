from piccolo.apps.migrations.auto.migration_manager import MigrationManager


ID = "2024-08-25T14:20:27:627608"
VERSION = "1.16.0"
DESCRIPTION = ""


async def forwards():
    manager = MigrationManager(
        migration_id=ID, app_name="komodo", description=DESCRIPTION
    )

    manager.rename_table(
        old_class_name="RegisteredUser",
        old_tablename="discord_user",
        new_class_name="RegisteredUser",
        new_tablename="registered_user",
        schema=None,
    )

    return manager
