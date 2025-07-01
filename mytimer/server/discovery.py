"""UDP discovery server used to locate the API on local networks."""

from __future__ import annotations

import asyncio
import contextlib
import os
import socket

BROADCAST_PORT = 9999
DISCOVERY_MESSAGE = b"DISCOVER_SERVER"
RESPONSE_MESSAGE = b"SERVER_HERE"


class DiscoveryServer:
    """Listen for discovery broadcasts and respond with server details."""

    def __init__(self, api_port: int, udp_port: int = BROADCAST_PORT) -> None:
        self.api_port = api_port
        self.udp_port = udp_port
        self._sock: socket.socket | None = None
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        """Start listening for discovery messages."""
        if self._task:
            return
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setblocking(False)
        try:
            sock.bind(("", self.udp_port))
        except OSError:
            sock.close()
            return
        self._sock = sock
        self._task = asyncio.create_task(self._serve())

    async def stop(self) -> None:
        """Stop the discovery service."""
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        if self._sock:
            self._sock.close()
        self._task = None
        self._sock = None

    async def _serve(self) -> None:
        assert self._sock is not None
        loop = asyncio.get_running_loop()
        while True:
            try:
                data, addr = await loop.sock_recvfrom(self._sock, 1024)
            except asyncio.CancelledError:
                break
            if data.startswith(DISCOVERY_MESSAGE):
                msg = RESPONSE_MESSAGE + b" " + str(self.api_port).encode()
                await loop.sock_sendto(self._sock, msg, addr)


def create_discovery_server() -> DiscoveryServer:
    """Factory reading environment variables for configuration."""
    port = int(os.environ.get("MYTIMER_API_PORT", "8000"))
    return DiscoveryServer(api_port=port)
