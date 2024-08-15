"""
This module contains the settings model and functions to load or initialize settings.
"""

from __future__ import annotations

import logging
import os
import sys
import tomllib
from functools import lru_cache

import semver
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

# SETTINGS_VERSION will be updated whenever fields are added, changed, or removed.
# This way we can handle migrations when loading settings from file.
SETTINGS_VERSION = "0.1.0"

USE_FILE = os.getenv("KOMODO_USE_FILE", "true").lower() in ("true", "1", "t")
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


class AITenorSettings(BaseModel):
    """Tenor settings."""

    api_key: str = ""


class AISettings(BaseModel):
    """AI settings."""

    openai_key: str = ""
    chatbot_channel_id: int = 0
    tenor: AITenorSettings = AITenorSettings()


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

    version: str = SETTINGS_VERSION

    discord: DiscordSettings = DiscordSettings()

    pnw: PnWSettings = PnWSettings()

    ai: AISettings = AISettings()

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

    @classmethod
    def load_or_initialize_settings(cls) -> Settings:
        """Load or initialize settings.

        Returns:
            Settings: The loaded or initialized settings.
        """
        settings = (
            cls.load_or_initialize_settings_from_file()
            if USE_FILE
            else cls.load_or_initialize_settings_from_env()
        )

        logger.info(
            "Using settings from %s",
            SETTINGS_FILE_PATH if USE_FILE else "environment variables",
        )

        settings.validate_essential_settings()

        return settings

    @classmethod
    def load_or_initialize_settings_from_file(cls) -> "Settings":
        """Load settings from file or initialize with defaults if the file does not exist.
        Creates the settings file if it doesn't exist and exits the application,
        prompting the user to update the settings.
        """
        if os.path.exists(SETTINGS_FILE_PATH):
            logger.debug("Loading settings from %s", SETTINGS_FILE_PATH)
            settings = (
                cls()
            )  # This will load settings from file due to the cls() behavior

            cls._validate_settings_version(settings)
            return settings

        else:
            logger.warning(
                "Settings file does not exist. Creating a new one with default settings."
            )
            settings = cls()
            settings.save_to_file(SETTINGS_FILE_PATH)
            logger.info(
                "Default settings saved to %s. Please update the settings file as needed and restart the application.",
                SETTINGS_FILE_PATH,
            )
            sys.exit(0)

    @classmethod
    def _validate_settings_version(cls, settings: "Settings") -> None:
        """Validates and handles the version of the settings file."""
        try:
            comparison = semver.compare(settings.version, SETTINGS_VERSION)
        except ValueError as e:
            logger.error(
                "Invalid version format in settings: %s. Exiting application.", e
            )
            sys.exit(1)

        if comparison < 0:
            logger.warning(
                "Settings file version is outdated. Automatically updating the settings file. "
                "You may need to update the settings manually."
            )
            settings.version = SETTINGS_VERSION
            settings.save_to_file(SETTINGS_FILE_PATH)
        elif comparison > 0:
            logger.error(
                "Settings file version (%s) is newer than the application version (%s). "
                "Please update the application or downgrade the settings file.",
                settings.version,
                SETTINGS_VERSION,
            )
            sys.exit(1)

    @classmethod
    def load_or_initialize_settings_from_env(cls) -> Settings:
        """Initialize settings using environment variables if provided."""
        logger.debug("Initializing settings using environment variables if provided")
        return cls()

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
