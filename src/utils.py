from datetime import datetime


def create_discord_timestamp(dt: datetime):
    return f"<t:{int(dt.timestamp())}:f>"
