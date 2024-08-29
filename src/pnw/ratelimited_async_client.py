"""A rate limited version of the API v3 client."""

import logging
from typing import Any

from aiolimiter import AsyncLimiter
from httpx import AsyncClient, HTTPStatusError, Response, codes

logger = logging.getLogger(__name__)


class RatelimitedAsyncClient(AsyncClient):
    """Custom client that extends httpx.AsyncClient with rate limiting."""

    def __init__(
        self,
        max_rate: int = 10,
        time_period: int = 10,
        timeout: int = 30,
        **kwargs: Any,
    ):
        """
        Args:
            max_rate: Represents the maximum number of requests that can be made in the time_period.
            time_period: Represents the rate limit time period in seconds.
            kwargs: Additional arguments to pass to the parent class.
        """
        super().__init__(timeout=timeout, **kwargs)

        self._max_rate = max_rate
        self._time_period = time_period

        self.limiter = AsyncLimiter(self._max_rate, self._time_period)

    async def request(self, *args: Any, **kwargs: Any) -> Response:
        """Make a request with rate limiting."""
        async with self.limiter:
            response = await super().request(*args, **kwargs)

        match response.status_code:
            case codes.OK:
                return response
            case codes.TOO_MANY_REQUESTS:
                # Artificially fill the rate limit bucket to prevent further requests.
                self.limiter._level = self._max_rate  # type: ignore # pylint: disable=protected-access
                return await self.request(*args, **kwargs)
            case _:
                raise HTTPStatusError(
                    f"HTTP status {response.status_code}",
                    request=response.request,
                    response=response,
                )
