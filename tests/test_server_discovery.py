import asyncio
import socket
import pytest

from mytimer.client.server_discovery import discover_server

class DummySocket:
    def __init__(self, *a, **k):
        self.sent = False
    def setsockopt(self, *a):
        pass
    def settimeout(self, t):
        pass
    def sendto(self, data, addr):
        self.sent = True
    def recvfrom(self, size):
        if self.sent:
            self.sent = False
            return b"SERVER_HERE 8765", ("127.0.0.1", 9999)
        raise socket.timeout
    def close(self):
        pass
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        pass

@pytest.mark.asyncio
async def test_discover_server_mock(monkeypatch):
    monkeypatch.setattr(socket, "socket", lambda *a, **k: DummySocket())
    servers = await discover_server(timeout=1, addr="127.0.0.1")
    assert ("127.0.0.1", 8765) in servers
