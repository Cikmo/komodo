"""
This module contains the settings model and functions to load or initialize settings.
"""

from __future__ import annotations

import logging
import os
import sys
import tomllib
from functools import lru_cache

import tomli_w
from pydantic import BaseModel
from pydantic_settings import (
    BaseSettings,
    EnvSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

logger = logging.getLogger(__name__)

USE_FILE = os.getenv("USE_FILE", "true").lower() in ("true", "1", "t")
SETTINGS_FILE_PATH = "settings.dev.toml" if __debug__ else "settings.toml"


class DiscordSettings(BaseModel):
    """Bot settings."""

    token: str = ""
    client_secret: str = ""

    bot_name: str = "Komodo"
    default_command_prefix: str = "!"
    developer_guild_id: int = 0


class PnWSettings(BaseModel):
    """PnW settings."""

    api_key: str = ""
    bot_key: str = ""
    username: str = ""
    password: str = ""


class LoggingStreamSettings(BaseModel):
    """Logging stream settings."""

    level: str = "INFO"
    level_discord: str = "INFO"

    datefmt: str = "%Y-%m-%d %H:%M:%S"
    format_info: str = (
        "\033[1;30m%(asctime)s\033[0m \033[1;34m%(levelname)-8s\033[0m \033[1;35m%(name)s\033[0m %(message)s"
    )
    format_debug: str = (
        "\033[1;30m%(asctime)s\033[0m \033[1;35m%(levelname)-8s\033[0m \033[1;35m%(name)s\033[0m %(message)s"
    )
    format_warning: str = (
        "\033[1;30m%(asctime)s\033[0m \033[1;33m%(levelname)-8s\033[0m \033[1;35m%(name)s\033[0m %(message)s"
    )
    format_error: str = (
        "\033[1;30m%(asctime)s\033[0m \033[1;31m%(levelname)-8s\033[0m \033[1;35m%(name)s\033[0m %(message)s"
    )
    format_critical: str = (
        "\033[1;30m%(asctime)s\033[0m \033[1;41m%(levelname)-8s\033[0m \033[1;35m%(name)s\033[0m %(message)s"
    )


class LoggingFileSettings(BaseModel):
    """Logging file settings."""

    path: str = ""
    level: str = "INFO"
    level_discord: str = "INFO"

    datefmt: str = "%Y-%m-%d %H:%M:%S"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


class LoggingSettings(BaseModel):
    """Logging settings."""

    stream: LoggingStreamSettings = LoggingStreamSettings()
    file: LoggingFileSettings = LoggingFileSettings()


class DatabaseSettings(BaseModel):
    """Database settings."""

    host: str = ""
    port: int = 5432
    database: str = ""
    user: str = ""
    password: str = ""


class Settings(BaseSettings):
    """Application settings."""

    file_version: int = 1

    discord: DiscordSettings = DiscordSettings()

    pnw: PnWSettings = PnWSettings()

    database: DatabaseSettings = DatabaseSettings()

    logging: LoggingSettings = LoggingSettings()

    model_config = SettingsConfigDict(
        env_prefix="komodo_",
        extra="ignore",
        toml_file=SETTINGS_FILE_PATH,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, EnvSettingsSource]:
        return (TomlConfigSettingsSource(settings_cls), EnvSettingsSource(settings_cls))

    def save_to_file(self, file_path: str | None = None):
        """Save settings to a file.

        Args:
            file_path: The path to the file to save the settings to.
            If not provided, use the default settings file path.

        Raises:
            ValueError: If the generated TOML is invalid.
        """

        file_path = file_path or SETTINGS_FILE_PATH

        toml = tomli_w.dumps(self.model_dump())

        # Validate toml
        try:
            tomllib.loads(toml)
        except tomllib.TOMLDecodeError as e:
            raise tomllib.TOMLDecodeError("Invalid TOML generated.") from e

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(toml)
                logger.info("Settings saved to %s", file_path)
        except IOError as e:
            logger.error("Failed to save settings to %s", file_path)
            raise e

    @classmethod
    def load_or_initialize_settings(cls) -> Settings:
        """Load or initialize settings.
        Args:
            use_file: A flag indicating whether to load settings from a file or use environment variables.

        Returns:
            Settings: The loaded or initialized settings.
        """

        if USE_FILE:
            settings_file_created = False

            if os.path.exists(path=SETTINGS_FILE_PATH):
                # Load settings from the settings file.

                settings = cls()

                logger.debug("Loading settings from %s", SETTINGS_FILE_PATH)
            else:
                # Create a new settings model, ignoring any environment variables and using the default values.
                settings = cls.model_construct()
                logger.debug("Initializing settings with default values")

                settings_file_created = True

            settings.save_to_file(SETTINGS_FILE_PATH)
            logger.info("Settings initialized and saved to %s", SETTINGS_FILE_PATH)

            if settings_file_created:
                cls.exit_due_to_new_file_created()

        else:
            # Create a new settings model, using environment variables if provided.
            settings = cls()
            logger.debug(
                "Initializing settings using environment variables if provided"
            )

        logger.info(
            "Using settings from %s",
            "environment variables" if not USE_FILE else f"{SETTINGS_FILE_PATH}",
        )

        settings.validate_essential_settings()

        return settings

    @staticmethod
    def exit_due_to_new_file_created():
        """Handle missing settings by informing the user and exiting."""
        logger.error(
            "Settings file not found.\n"
            "A new settings file has been created with default values. Please update it with the "
            "correct values before restarting the application."
        )
        sys.exit(1)

    def validate_essential_settings(self) -> None:
        """Validate the settings. If any essential settings are missing,
        print an error message and exit."""
        errors: list[str] = []

        # List of required fields with their attribute paths
        required_fields = [
            "discord.token",
            "discord.client_secret",
            "database.database",
            "database.host",
            "database.user",
        ]

        for field_path in required_fields:
            field_value = self
            for attr in field_path.split("."):
                field_value = getattr(field_value, attr)
            if field_value == "":
                errors.append(field_path)

        if any(errors):
            logger.error(
                "The following essential settings have not been set:\n- %s",
                "\n- ".join(errors),
            )
            sys.exit(1)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get the application settings. If the settings have not been loaded, load them.

    Returns:
        Settings: The application settings.
    """
    return Settings.load_or_initialize_settings()
