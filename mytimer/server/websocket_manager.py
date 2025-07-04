from __future__ import annotations

"""Utility class to manage WebSocket connections and broadcast messages."""


from typing import Set, Any
from fastapi import WebSocket, WebSocketDisconnect

class WebSocketManager:
    """Manage connected WebSocket clients."""

    def __init__(self) -> None:
        self._websockets: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        """Accept and register a new WebSocket connection."""
        await ws.accept()
        self._websockets.add(ws)

    def disconnect(self, ws: WebSocket) -> None:
        """Remove a WebSocket from the registry."""
        self._websockets.discard(ws)

    async def broadcast_json(self, data: Any) -> None:
        """Send ``data`` to all connected clients as JSON."""
        for ws in list(self._websockets):
            try:
                await ws.send_json(data)
            except WebSocketDisconnect:
                self._websockets.discard(ws)

    async def send_json(self, ws: WebSocket, data: Any) -> None:
        """Send ``data`` to a single ``ws`` connection as JSON."""
        try:
            await ws.send_json(data)
        except WebSocketDisconnect:
            self._websockets.discard(ws)

    async def broadcast_text(self, message: str) -> None:
        """Send a plain text ``message`` to all connected clients."""
        for ws in list(self._websockets):
            try:
                await ws.send_text(message)
            except WebSocketDisconnect:
                self._websockets.discard(ws)

    async def send_text(self, ws: WebSocket, message: str) -> None:
        """Send a plain text ``message`` to a single ``ws`` connection."""
        try:
            await ws.send_text(message)
        except WebSocketDisconnect:
            self._websockets.discard(ws)
