"""
This module contains the settings model and functions to load or initialize settings.
"""

from __future__ import annotations

import logging
import os

import tomllib
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

SETTINGS_FILE_PATH = "settings.toml"


class DiscordSettings(BaseModel):
    """Bot settings."""

    token: str = ""
    client_id: str = ""
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

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


class Settings(BaseSettings):
    """Application settings."""

    file_version: int = 1

    discord: DiscordSettings = DiscordSettings()

    pnw: PnWSettings = PnWSettings()

    logging: LoggingSettings = LoggingSettings()

    model_config = SettingsConfigDict(
        env_prefix="komodo_", extra="ignore", toml_file=SETTINGS_FILE_PATH
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
            raise ValueError(f"Invalid TOML generated.") from e

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(toml)
            logger.info("Settings saved to %s", file_path)


def load_or_initialize_settings(use_file: bool) -> Settings:
    """Load or initialize settings.
    Args:
        use_file: A flag indicating whether to load settings from a file or use environment variables.

    Returns:
        Settings: The loaded or initialized settings.
    """

    if use_file:
        if os.path.exists(path=SETTINGS_FILE_PATH):
            # Load settings from the settings file.

            print("test")

            settings = Settings()

            logger.debug("Loading settings from %s", SETTINGS_FILE_PATH)
        else:
            # Create a new settings model, ignoring any environment variables and using the default values.
            settings = Settings.model_construct()
            logger.debug("Initializing settings with default values")

        settings.save_to_file(SETTINGS_FILE_PATH)
        logger.info("Settings initialized and saved to %s", SETTINGS_FILE_PATH)
    else:
        # Create a new settings model, using environment variables if provided.
        settings = Settings()
        logger.debug("Initializing settings using environment variables if provided")

    logger.info(
        "Using settings from %s",
        "environment variables" if not use_file else f"{SETTINGS_FILE_PATH}",
    )

    return settings
