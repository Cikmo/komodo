"""
Configuration for Piccolo ORM.
"""

from piccolo.conf.apps import AppRegistry
from piccolo.engine.postgres import PostgresEngine

from src.config.settings import get_settings

settings = get_settings()

DB = PostgresEngine(
    config={
        "database": settings.database.database,
        "user": settings.database.user,
        "password": settings.database.password,
        "host": settings.database.host,
        "port": settings.database.port,
    }
)


# A list of paths to piccolo apps
APP_REGISTRY = AppRegistry(apps=["src.piccolo_app"])
