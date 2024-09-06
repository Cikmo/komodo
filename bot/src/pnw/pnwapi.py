"""
This module is used to interact with the Politics and War API.
"""

from .api_v3 import Client


class PnwAPI:
    """
    Politics and War API client.
    """

    def __init__(self, api_key: str, bot_key: str):
        self._api_key = api_key
        self._bot_key = bot_key

        self.v3 = Client(
            url=f"https://api.politicsandwar.com/graphql?api_key={api_key}",
            headers={
                "X-Bot-Key": bot_key,
                "X-Api-Key": api_key,
            },
        )
