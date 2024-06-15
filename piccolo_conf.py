"""
Configuration for Piccolo ORM.
"""

from piccolo.conf.apps import AppRegistry
from piccolo.engine.postgres import PostgresEngine

from src.config.settings import get_settings

settings = get_settings()

try:
    DB = PostgresEngine(
        config={
            "database": settings.database.database,
            "user": settings.database.user,
            "password": settings.database.password,
            "host": settings.database.host,
            "port": settings.database.port,
        }
    )
except ConnectionRefusedError:
    raise ConnectionRefusedError(
        "Could not connect to the database. Check that the database is running, "
        "and that the connection settings are correct."
    ) from None


# A list of paths to piccolo apps
APP_REGISTRY = AppRegistry(apps=["piccolo_app"])
