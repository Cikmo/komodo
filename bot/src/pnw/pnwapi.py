"""
This module is used to interact with the Politics and War API.
"""

from logging import getLogger

from .api_v3 import Client
from .subscriptions.subscription import Subscriptions

logger = getLogger(__name__)


class PnwAPI:
    """
    Politics and War API client.
    """

    def __init__(
        self,
        api_key: str,
        bot_key: str,
        last_subscription_event: tuple[int, int] | None = None,
    ):
        self._api_key = api_key
        self._bot_key = bot_key

        self.v3 = Client(
            url=f"https://api.politicsandwar.com/graphql?api_key={api_key}",
            headers={
                "X-Bot-Key": bot_key,
                "X-Api-Key": api_key,
            },
        )

        self.subscriptions = Subscriptions(api_key, last_subscription_event)
