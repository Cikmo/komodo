"""
Various utility functions and classes.
"""

import asyncio
import logging
from functools import wraps
from time import perf_counter
from typing import Any, Callable


class Timer:
    """Context manager to measure the time taken by a block of code."""

    def __init__(
        self, operation_name: str | None = None, logger: logging.Logger | None = None
    ):
        """Initializes the Timer object.

        Args:
            operation_name: The name of the operation being timed.
            logger: Provide a logger to log the elapsed time automatically. If not
                provided, the elapsed time will not be logged.
        """
        self.operation_name = operation_name
        self._logger = logger
        self._start_time: float | None = None
        self._final_elapsed_time: float | None = None

    @property
    def elapsed(self) -> float:
        """Return the elapsed time since the context manager was entered."""
        if self._start_time is None:
            raise RuntimeError("The context manager has not been entered yet.")
        if self._final_elapsed_time is not None:
            return self._final_elapsed_time
        return perf_counter() - self._start_time

    def __enter__(self):
        self._start_time = perf_counter()
        self._final_elapsed_time = None
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: BaseException | None,
    ):
        if self._start_time is None:
            raise RuntimeError("The context manager has not been entered yet.")
        self._final_elapsed_time = perf_counter() - self._start_time
        if self._logger:
            self._logger.info(
                "%s took %.6f seconds",
                self.operation_name or "Operation",
                self._final_elapsed_time,
            )

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """Allows the Timer to be used as a decorator."""

        if self.operation_name is None:
            self.operation_name = func.__name__

        if self._logger is None:
            self._logger = logging.getLogger(func.__module__)

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            if not asyncio.iscoroutinefunction(func):
                with Timer(operation_name=self.operation_name, logger=self._logger):
                    return func(*args, **kwargs)

            async def tmp():
                with Timer(operation_name=self.operation_name, logger=self._logger):
                    return await func(*args, **kwargs)

            return tmp()

        return wrapper
