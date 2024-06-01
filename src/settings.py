"""
This module contains the settings model and functions to load or initialize settings.
"""

from __future__ import annotations
import logging
import os

from pydantic import BaseModel

logger = logging.getLogger(__name__)


# TODO: Look into using pydantic's BaseSettings instead of BaseModel
# https://docs.pydantic.dev/latest/concepts/pydantic_settings/


class BotSettings(BaseModel):
    """Bot settings."""

    token: str = "YOUR_BOT_TOKEN"
    prefix: str = "!"


class PnWSettings(BaseModel):
    """PnW settings."""

    api_key: str = "YOUR_API_KEY"
    bot_key: str | None = None


class Settings(BaseModel):
    """Application settings."""

    _settings_version_: int = (
        1  # Increment when breaking changes are made, like changing the type of a field, etc.
    )
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    bot: BotSettings = BotSettings()

    pnw: PnWSettings = PnWSettings()

    def save_to_file(self, file_path: str):
        """Save settings to a file.

        Args:
            file_path: The path to the settings file. Defaults to "settings.json".
        """
        settings_json = self.model_dump_json(indent=4)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(settings_json)
            logger.info("Settings saved to %s", file_path)

    @classmethod
    def load_from_file(cls, file_path: str) -> "Settings":
        """Load settings from a file.

        Args:
            file_path: The path to the settings file. Defaults to "settings.json".

        Returns:
            The loaded settings.
        """
        with open(file_path, "r", encoding="utf-8") as f:
            settings_json = f.read()
            settings = cls.model_validate_json(settings_json)
            logger.info("Settings loaded from %s", file_path)
            return settings


def load_or_initialize_settings(file_path: str):
    """Load or initialize settings. If the file does not exist, default
    settings are created and saved. If new settings are added to the model,
    they will be added to the file with default values.

    Args:
        file_path: The path to the settings file. Defaults to "settings.json".
    """

    if os.path.exists(file_path):
        settings = Settings.load_from_file(file_path)
    else:
        settings = Settings()
        logger.info("Default settings created")

    settings.save_to_file(file_path)

    return settings
