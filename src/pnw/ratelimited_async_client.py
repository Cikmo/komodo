"""A rate limited version of the API v3 client."""

import asyncio
import logging
import time
from typing import Any

from httpx import AsyncClient, Response
from httpx import _types as httpx_types  # type: ignore

logger = logging.getLogger(__name__)


class RateLimit:
    """A class to handle rate limiting."""

    def __init__(self):
        self.limit: int | None = None
        self.remaining: int | None = None
        self.reset: int | None = None
        self.interval: int | None = None

    @property
    def initialized(self) -> bool:
        """Check if the rate limit has been initialized."""
        return (
            self.limit is not None
            and self.remaining is not None
            and self.reset is not None
            and self.interval is not None
        )

    def initialize(self, headers: httpx_types.HeaderTypes) -> None:
        """Initialize the rate limit.

        Args:
            headers: The headers from the response.
        """
        self.limit = self._get_int_or_none(headers.get("X-RateLimit-Limit"))  # type: ignore
        self.remaining = self._get_int_or_none(headers.get("X-RateLimit-Remaining"))  # type: ignore
        self.reset = self._get_int_or_none(headers.get("X-RateLimit-Reset"))  # type: ignore
        self.interval = self._get_int_or_none(headers.get("X-RateLimit-Interval"))  # type: ignore

    def hit(self):
        """Hit the rate limit.

        Returns:
            int: The number of seconds until the rate limit resets.
        """
        if (
            self.limit is None
            or self.remaining is None
            or self.reset is None
            or self.interval is None
        ):
            return 0

        current_time = int(time.time())

        if current_time > self.reset:
            self.remaining = self.limit - 1
            self.reset = int(current_time + 1 + self.interval)
            return 0

        self.remaining -= 1

        if self.remaining <= 0:
            return int(self.reset - current_time) + 1
        return 0

    def handle_429(self, reset: str | None) -> float:
        """Handle a 429 response.

        Args:
            reset: The time at which the rate limit will reset.

        Returns:
            float: The number of seconds until the rate limit resets.
        """
        self.remaining = 0
        self.reset = (
            self._get_int_or_none(reset)
            or self.reset
            or int(time.time() + (self.interval or 60))
        )
        return self.reset - time.time()

    def _get_int_or_none(self, value: str | None) -> int | None:
        return int(value) if value is not None else None


class RatelimitedAsyncClient(AsyncClient):
    """Custom client that extends httpx.AsyncClient with rate limiting."""

    def __init__(
        self,
        *args: Any,
        timeout: int = 30,
        **kwargs: Any,
    ):
        """
        Args:
            max_rate: Represents the maximum number of requests that can be made in the time_period.
            time_period: Represents the rate limit time period in seconds.
            kwargs: Additional arguments to pass to the parent class.
        """
        super().__init__(*args, timeout=timeout, **kwargs)
        self.rate_limit = RateLimit()

    async def request(
        self, *args: Any, headers: httpx_types.HeaderTypes, **kwargs: Any
    ) -> Response:
        """Make a request with rate limiting."""
        if not self.rate_limit.initialized:
            self.rate_limit.initialize(headers)

        if wait := self.rate_limit.hit():
            print(f"Rate limit hit. Waiting {wait} seconds.")
            await asyncio.sleep(wait)

        response = await super().request(*args, headers=headers, **kwargs)

        if response.status_code == 429:
            reset = response.headers.get("X-RateLimit-Reset")
            if reset is None:
                logger.error("429 response missing X-RateLimit-Reset header.")
                return response
            wait = self.rate_limit.handle_429(reset)
            print(f"429 hit. Waiting {wait} seconds.")
            await asyncio.sleep(wait)
            return await self.request(*args, headers=headers, **kwargs)

        return response
