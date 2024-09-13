"""Connection client."""

import asyncio
import json
import logging
from collections import defaultdict
from enum import Enum
from random import random
from typing import Any, Callable, Coroutine

import aiohttp
from pydantic import ValidationError

from .models import ConnectionEstablishedEvent, PusherEvent
from .types import Callback, EventCallbacks, EventData

MAX_WAIT_SECONDS = 120


class Connection:  # pylint: disable=too-many-instance-attributes
    """
    Implements pusher protocol 7 described in
    https://pusher.com/docs/channels/library_auth_reference/pusher-websockets-protocol/
    """

    class State(Enum):
        """Connection states"""

        IDLE = 1
        CONNECTED = 2
        FAILED = 3
        CLOSED = 4

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        url: str,
        callback: Callable[..., Coroutine[Any, Any, None]],
        log: logging.Logger,
        use_pusher_ping: bool = True,
        **kwargs: Any,
    ):
        self._loop = loop
        self._url = url
        self._callback = callback
        self._log = log
        self._use_pusher_ping = use_pusher_ping
        self._websocket_params = kwargs

        self._event_callbacks: EventCallbacks = defaultdict(dict)

        self._connection_attempts = 0
        # stop signal to break infinite loop in _run_forever
        self._stop = False
        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self.socket_id = None
        # https://pusher.com/docs/channels/library_auth_reference/pusher-websockets-protocol/#recommendations-for-client-libraries
        self._activity_timeout = 120
        self._pong_timeout = 30
        self.state = self.State.IDLE
        self._last_message_time: float | None = None

        self.bind("pusher:connection_established", self._handle_connection)
        self.bind("pusher:connection_failed", self._handle_failure)
        self.bind("pusher:error", self._handle_error)
        self.bind("pusher:pong", self._handle_pong)

    async def open(self):
        """Open connection and wait until it is established."""
        self._loop.create_task(self._run_forever())

        while self.state != self.State.CONNECTED:
            await asyncio.sleep(1)

        if self._use_pusher_ping:
            self._loop.create_task(self._periodic_ping())

    async def close(self):
        """Close connection."""
        self._stop = True
        if self.state == self.State.CONNECTED and self._ws:
            await self._ws.close()

    async def _run_forever(self):
        async with aiohttp.ClientSession() as session:
            while not self._stop:
                try:
                    await self._connect(session)
                except aiohttp.ClientError:
                    self._log.exception("Exception while connecting to web socket")
                    self._connection_attempts += 1
        self._log.info("End of forever")

    async def _connect(self, session: aiohttp.ClientSession):
        self._log.info("Pusher connecting...")

        wait_seconds = self._get_wait_time(self._connection_attempts)
        self._log.info(
            f"Waiting for {wait_seconds}s, # attempts: {self._connection_attempts}"
        )
        await asyncio.sleep(wait_seconds)

        async with session.ws_connect(
            self._url,
            heartbeat=self._activity_timeout if not self._use_pusher_ping else None,
            **self._websocket_params,
        ) as ws:
            # internally aiohttp.ClientWebSocketResponse uses heartbeat/2 as pong timeout but pusher protocol advise 30s
            ws._pong_heartbeat = self._pong_timeout  # type: ignore # pylint: disable=protected-access
            self._ws = ws
            await self._dispatch(ws)

    async def _dispatch(self, ws: aiohttp.ClientWebSocketResponse) -> None:
        while True:
            msg = await ws.receive()
            self._log.debug(f"Websocket message: {msg}")
            self._last_message_time = self._loop.time()  # Update last message time
            if msg.type == aiohttp.WSMsgType.TEXT:
                event = json.loads(msg.data)
                await self._handle_event(event)
            else:
                self.state = self.State.CLOSED
                self._log.info(f"Exiting dispatch with message: {msg}")
                if msg.type == aiohttp.WSMsgType.CLOSE:
                    if isinstance(msg.data, int):
                        code = msg.data
                        # 4000-4099: The connection SHOULD NOT be re-established unchanged.
                        if 4000 <= code < 4100:
                            self._stop = True
                        # 4100-4199: The connection SHOULD be re-established after backing off.
                        # The back-off time SHOULD be at least 1 second in duration and MAY be
                        # exponential in nature on consecutive failures.
                        elif 4100 <= code < 4200:
                            self._connection_attempts += 1
                        # 4200-4299: The connection SHOULD be re-established immediately.
                        elif 4200 <= code < 4300:
                            self._connection_attempts = 0
                    else:
                        # Unknown closing, it sometimes happens. Try to reconnect anyway
                        self._connection_attempts = 0
                    await ws.close()
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    self._log.error(f"Error received {ws.exception()}")
                    self._connection_attempts = 0
                break

    async def _handle_event(self, raw_event: dict[str, Any]):

        try:
            event = PusherEvent(**raw_event)
        except ValidationError as e:
            self._log.error(f"Unexpected event: {e}")
            return

        if event.channel:
            # asyncio.create_task(self._callback(event.channel, event.name, event.data))
            await self._callback(event.channel, event.name, event.data)
            return

        # If the event is not tied to a channel, call the connection's event handler.
        if event.name in self._event_callbacks:
            for callback, (args, kwargs) in self._event_callbacks[event.name].items():
                try:
                    # asyncio.create_task(callback(event.data, *args, **kwargs))
                    await callback(event.data, *args, **kwargs)
                except Exception:  # type: ignore # pylint: disable=broad-except
                    self._log.exception(f"Exception in callback: {event.data}")
            return

        self._log.warning(f"Unhandled event: {event}")

    async def send_event(self, event: PusherEvent):
        """Send a pusher event."""

        retry_count = 5
        while retry_count > 0 and self.state != self.State.CONNECTED:
            await asyncio.sleep(1)
            retry_count -= 1

        if not self._ws:
            raise ValueError("Websocket not connected")

        await self._ws.send_str(event.model_dump_json(by_alias=True, exclude_none=True))

    async def _handle_pong(self, _: Any):
        self._log.info("Received pong")

    async def send_ping(self):
        """Send a ping message to the server."""
        await self.send_event(PusherEvent(event="pusher:ping"))

    async def _periodic_ping(self):
        """Periodically send ping messages to keep the connection alive."""
        while not self._stop:
            if self.state == self.State.CONNECTED:
                now = self._loop.time()

                if not self._last_message_time:
                    self._last_message_time = now

                # sleep until next ping. If the time since last message is greater than the ping interval
                # then send a ping message
                await asyncio.sleep(
                    max(
                        0,
                        self._activity_timeout - (now - self._last_message_time),
                    )
                )

                # if recieved message within ping interval, continue to next iteration since we don't need to send ping
                now = self._loop.time()
                if now - self._last_message_time < self._activity_timeout:
                    continue

                self._log.info("Sending ping")
                await self.send_ping()
                await asyncio.sleep(self._pong_timeout)
            else:
                await asyncio.sleep(1)

    async def _handle_connection(self, data: EventData):
        if not data:
            raise ValueError("Invalid connection established event")
        if not isinstance(data, dict):
            raise ValueError("Invalid connection established event")

        event = ConnectionEstablishedEvent(**data)

        self.socket_id = event.socket_id
        self._activity_timeout = event.activity_timeout
        # force to update heartbeat
        self._ws._heartbeat = self._activity_timeout  # type: ignore # pylint: disable=protected-access
        self.state = self.State.CONNECTED
        self._log.info(f"Connection established: {data}")

    async def _handle_failure(self, data: EventData):
        self.state = self.State.FAILED
        self._log.error(f"Connection failed: {data}")

    async def _handle_error(self, data: EventData):
        self._log.error(f"Pusher error: {data}")

    def bind(
        self,
        event_name: str,
        callback: Callback,
        *args: Any,
        **kwargs: Any,
    ):
        """Bind callback to event.

        Args:
            event_name: Event name to bind to.
            callback: Callback to call when event is triggered.
        """
        self._event_callbacks[event_name][callback] = (args, kwargs)

    def unbind(self, event_name: str, callback: Callback):
        """Unbind callback from event.

        Args:
            event_name: Event name to unbind from.
            callback: Callback to unbind.
        """
        del self._event_callbacks[event_name][callback]

    def is_connected(self):
        """Check if connection is established."""
        return self.state == self.State.CONNECTED

    @staticmethod
    def _get_wait_time(num_attempts: int):
        if num_attempts <= 0:
            return 0
        # wait time should at least 1 seconds
        seconds = round(random() * (2 ** (num_attempts) - 1)) + 1
        return min(seconds, MAX_WAIT_SECONDS)
