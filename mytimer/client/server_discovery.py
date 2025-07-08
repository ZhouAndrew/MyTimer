"""Client side helper for discovering MyTimer servers on the local network."""
from __future__ import annotations

import asyncio
import socket

BROADCAST_PORT = 9999
BROADCAST_ADDR = "255.255.255.255"
DISCOVERY_MESSAGE = b"DISCOVER_SERVER"
RESPONSE_MESSAGE = b"SERVER_HERE"
TIMEOUT = 3

async def discover_server(timeout: int = TIMEOUT, port: int = BROADCAST_PORT, addr: str = BROADCAST_ADDR) -> list[tuple[str, int]]:
    """Broadcast a UDP discovery request and return responding server addresses."""
    loop = asyncio.get_running_loop()
    found: list[tuple[str, int]] = []
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(timeout)
        try:
            sock.sendto(DISCOVERY_MESSAGE, (addr, port))
        except OSError:
            sock.sendto(DISCOVERY_MESSAGE, ("127.0.0.1", port))
        start = loop.time()
        while True:
            remain = timeout - (loop.time() - start)
            if remain <= 0:
                break
            sock.settimeout(remain)
            try:
                data, raddr = sock.recvfrom(1024)
            except socket.timeout:
                break
            if data.startswith(RESPONSE_MESSAGE):
                parts = data.decode().split()
                srv_port = int(parts[1]) if len(parts) > 1 else 8000
                found.append((raddr[0], srv_port))
    return found
