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
    command_prefix: str = "!"
    developer_guild_id: int = 0


class PnWSettings(BaseModel):
    """PnW settings."""

    api_key: str = ""
    bot_key: str = ""
    username: str = ""
    password: str = ""


class LoggingSettings(BaseModel):
    """Logging settings."""

    stream_level_komodo: str = "INFO"
    stream_level_discord: str = "INFO"

    file_path: str = ""
    file_level: str = "INFO"
    file_level_discord: str = "INFO"


class Settings(BaseSettings):
    """Application settings."""

    file_version: int = 1

    discord: DiscordSettings = DiscordSettings()

    pnw: PnWSettings = PnWSettings()

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
            file_path: The path to the file to save the settings to. If not provided, use the default settings file path.

        Raises:
            ValueError: If the generated TOML is invalid.
        """

        file_path = file_path or SETTINGS_FILE_PATH

        toml = tomli_w.dumps(self.model_dump())

        # Validate toml
        try:
            tomllib.loads(toml)
        except tomllib.TOMLDecodeError as e:
            raise tomllib.TOMLDecodeError(f"Invalid TOML generated.") from e

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
            "A new settings file has been created with default values. Please update it with the correct values "
            "before restarting the application."
        )
        sys.exit(1)

    def validate_essential_settings(self) -> None:
        """Validate the settings. If any essential settings are missing, print an error message and exit."""
        errors: list[str] = []

        if self.discord.token == "":
            errors.append("discord token")
        if self.discord.client_secret == "":
            errors.append("discord client_secret")

        if any(errors):
            logger.error(
                "The following essential settings have not been set:\n- "
                + "\n- ".join(errors)
            )
            exit(1)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get the application settings. If the settings have not been loaded, load them.

    Returns:
        Settings: The application settings.
    """
    return Settings.load_or_initialize_settings()
