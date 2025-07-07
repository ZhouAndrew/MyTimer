"""Client-side SyncService for real-time timer updates via WebSocket.

This module provides a simple client that keeps a local copy of timer states
synchronized with the server via WebSocket, while also offering convenience
methods to control timers through the REST API.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Dict, Optional
import contextlib

import httpx
import websockets


@dataclass
class TimerState:
    """Representation of a single timer's state."""

    duration: float
    remaining: float
    running: bool
    finished: bool


class SyncService:
    """Maintain WebSocket sync with the API server and expose REST helpers."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.ws_url = self.base_url.replace("http", "ws", 1) + "/ws"
        self.client = httpx.AsyncClient(base_url=self.base_url)
        self.state: Dict[str, TimerState] = {}
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._recv_task: Optional[asyncio.Task[None]] = None
        self.connected = False

    async def connect(self) -> None:
        """Establish the WebSocket connection and start the receive loop."""
        self._ws = await websockets.connect(self.ws_url)
        self.connected = True
        self._recv_task = asyncio.create_task(self._recv_loop())

    async def _recv_loop(self) -> None:
        assert self._ws is not None
        try:
            async for message in self._ws:
                data = json.loads(message)
                if isinstance(data, dict) and "type" in data:
                    if data.get("type") == "update":
                        tid = str(data["timer_id"])
                        state = self.state.get(tid)
                        if state:
                            state.remaining = data["remaining"]
                            state.running = data.get("running", state.running)
                            state.finished = data["finished"]
                            state.duration = data.get("duration", state.duration)
                        else:
                            self.state[tid] = TimerState(
                                duration=data.get("duration", data["remaining"]),
                                remaining=data["remaining"],
                                running=data.get("running", not data["finished"]),
                                finished=data["finished"],
                            )
                else:
                    self.state = {
                        str(tid): TimerState(**info) for tid, info in data.items()
                    }
        except websockets.ConnectionClosed:
            pass

    async def close(self) -> None:
        """Close WebSocket connection and HTTP client."""
        if self._ws is not None:
            await self._ws.close()
            self.connected = False
        if self._recv_task is not None:
            self._recv_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._recv_task
        await self.client.aclose()

    async def create_timer(self, duration: float) -> int:
        resp = await self.client.post("/timers", params={"duration": duration})
        resp.raise_for_status()
        return resp.json()["timer_id"]

    async def pause_timer(self, timer_id: int) -> None:
        resp = await self.client.post(f"/timers/{timer_id}/pause")
        resp.raise_for_status()

    async def resume_timer(self, timer_id: int) -> None:
        resp = await self.client.post(f"/timers/{timer_id}/resume")
        resp.raise_for_status()

    async def remove_timer(self, timer_id: int) -> None:
        resp = await self.client.delete(f"/timers/{timer_id}")
        resp.raise_for_status()

    async def tick(self, seconds: float) -> None:
        resp = await self.client.post("/tick", params={"seconds": seconds})
        resp.raise_for_status()
