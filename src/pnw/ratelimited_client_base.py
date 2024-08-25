"""A rate limited version of the API v3 client."""

import asyncio
from types import FunctionType
from typing import Any, Callable

from aiolimiter import AsyncLimiter

from src.pnw.api_v3.async_base_client import AsyncBaseClient


def rate_limiter_decorator(rate_limiter: AsyncLimiter):
    """Decorator to apply the rate limiter to a method."""

    def decorator(func: Callable[..., Any]):
        async def wrapper(*args: Any, **kwargs: Any):
            async with rate_limiter:
                print(f"Rate limited call to {func.__name__}")
                return await func(*args, **kwargs)

        return wrapper

    return decorator


class RateLimitedMeta(type):
    """Metaclass that wraps all async methods with a rate limiter."""

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        dct: dict[str, Any],
        max_rate: int = 60,
        time_period: int = 60,
    ):
        """Wrap all async methods with a rate limiter."""

        rate_limiter = AsyncLimiter(max_rate=max_rate, time_period=time_period)
        dct["rate_limiter"] = rate_limiter

        for attr_name, attr_value in dct.items():
            if isinstance(attr_value, FunctionType) and asyncio.iscoroutinefunction(
                attr_value
            ):
                dct[attr_name] = rate_limiter_decorator(rate_limiter)(attr_value)

        return super().__new__(mcs, name, bases, dct)


class AsyncBaseClientRatelimited(
    AsyncBaseClient, metaclass=RateLimitedMeta, max_rate=60, time_period=60
):
    """A rate limited version of the API v3 client base."""

    rate_limiter: AsyncLimiter
