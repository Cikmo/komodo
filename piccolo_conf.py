from piccolo.conf.apps import AppRegistry
from piccolo.engine.postgres import PostgresEngine


DB = PostgresEngine(
    config={
        "database": "test",
        "user": "postgres",
        "password": "password",
        "host": "localhost",
        "port": 5432,
    }
)


# A list of paths to piccolo apps
# e.g. ['blog.piccolo_app']
APP_REGISTRY = AppRegistry(apps=["src.piccolo_app"])
