"""A rate limited version of the API v3 client."""

from typing import Any

from aiolimiter import AsyncLimiter
from httpx import AsyncClient
from httpx import _types as httpx_types  # type: ignore - cause of private import


class RatelimitedAsyncClient(AsyncClient):
    """Custom client that extends httpx.AsyncClient with rate limiting."""

    def __init__(
        self,
        *args: Any,
        max_rate: int = 60,
        time_period: int = 60,
        timeout: int = 30,
        **kwargs: Any
    ):
        """
        Args:
            max_rate: Represents the maximum number of requests that can be made in the time_period.
            time_period: Represents the rate limit time period in seconds.
            kwargs: Additional arguments to pass to the parent class.
        """
        self.rate_limiter = AsyncLimiter(max_rate=max_rate, time_period=time_period)
        super().__init__(*args, timeout=timeout, **kwargs)

    async def request(
        self, *args: Any, headers: httpx_types.HeaderTypes | None = None, **kwargs: Any
    ):
        async with self.rate_limiter:
            return await super().request(*args, **kwargs)
