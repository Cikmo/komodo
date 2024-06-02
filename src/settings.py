"""
This module contains the settings model and functions to load or initialize settings.
"""

from __future__ import annotations

import logging
import os
from typing import Tuple, Type

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


class BotSettings(BaseModel):
    """Bot settings."""

    token: str = ""
    prefix: str = "!"


class PnWSettings(BaseModel):
    """PnW settings."""

    api_key: str = ""
    bot_key: str = ""


class LoggingSettings(BaseModel):
    """Logging settings."""

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


class Settings(BaseSettings):
    """Application settings."""

    file_version: int = 1

    bot: BotSettings = BotSettings()

    pnw: PnWSettings = PnWSettings()

    logging: LoggingSettings = LoggingSettings()

    model_config = SettingsConfigDict(
        env_prefix="komodo_", extra="ignore", toml_file=SETTINGS_FILE_PATH
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, EnvSettingsSource]:
        return (TomlConfigSettingsSource(settings_cls), EnvSettingsSource(settings_cls))

    def save_to_file(self, file_path: str | None = None):
        """Save settings to a file.

        Args:
            file_path: The path to the file to save the settings to. If not provided, use the default settings file path.
        """

        file_path = file_path or SETTINGS_FILE_PATH

        toml = tomli_w.dumps(self.model_dump())
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(toml)
            logger.info("Settings saved to %s", file_path)


def load_or_initialize_settings(use_file: bool) -> Settings:
    """Load or initialize settings. If a file path is provided, load settings from the file.
    Otherwise, initialize settings using environment variables. Any settings not provided by
    the file or environment variables will use the default values.

    Args:
        file_path: The path to the settings file.

    Returns:
        Settings: The loaded or initialized settings.
    """

    settings = Settings()

    if use_file:
        if os.path.exists(path=SETTINGS_FILE_PATH):
            # Load settings from the provided file.
            settings = Settings()
            print("settings loaded from file")
        else:
            # Create a new settings model, ignoring any environment variables and using the default values.
            settings = Settings.model_construct()

        settings.save_to_file(SETTINGS_FILE_PATH)
    else:
        # Create a new settings model, using environment variables if provided.
        settings = Settings()

    return settings
