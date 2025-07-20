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
    """Maintain timer state synchronization via WebSocket or HTTP polling."""

    def __init__(
        self,
        base_url: str,
        reconnect_interval: float = 1.0,
        *,
        use_websocket: bool = True,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.ws_url = self.base_url.replace("http", "ws", 1) + "/ws"
        self.client = httpx.AsyncClient(base_url=self.base_url)
        self.state: Dict[str, TimerState] = {}
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._recv_task: Optional[asyncio.Task[None]] = None
        self._running = False
        self.reconnect_interval = reconnect_interval
        self.use_websocket = use_websocket
        self.connected = False


    async def connect(self) -> None:
        """Start syncing timer state using WebSocket or HTTP polling."""
        if self._recv_task:
            return
        self._running = True
        if self.use_websocket:
            self._ws = await websockets.connect(self.ws_url)
            self.connected = True
            self._recv_task = asyncio.create_task(self._recv_loop())
        else:
            self._recv_task = asyncio.create_task(self._poll_loop())
        await self._fetch_state()

    async def _fetch_state(self) -> None:
        resp = await self.client.get("/timers")
        resp.raise_for_status()
        data = resp.json()
        self.state = {str(tid): TimerState(**info) for tid, info in data.items()}

    def _handle_message(self, message: str) -> None:
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

    async def _recv_loop(self) -> None:
        while self._running:
            try:
                if self._ws is None:
                    self._ws = await websockets.connect(self.ws_url)
                    await self._fetch_state()
                async for message in self._ws:
                    self._handle_message(message)
            except websockets.ConnectionClosed:
                if not self._running:
                    break
            except Exception:
                if not self._running:
                    break
            finally:
                if self._ws:
                    with contextlib.suppress(Exception):
                        await self._ws.close()
                self._ws = None
            if self._running:
                await asyncio.sleep(self.reconnect_interval)

    async def _poll_loop(self) -> None:
        while self._running:
            try:
                await self._fetch_state()
            except Exception:
                if not self._running:
                    break
            await asyncio.sleep(self.reconnect_interval)

    async def close(self) -> None:
        """Close WebSocket connection and HTTP client."""
        self._running = False
        if self._ws is not None:
            await self._ws.close()
            self._ws = None
            self.connected = False
        if self._recv_task is not None:
            self._recv_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._recv_task
            self._recv_task = None
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

    async def remove_all_timers(self) -> None:
        resp = await self.client.delete("/timers")
        resp.raise_for_status()

    async def pause_all(self) -> None:
        resp = await self.client.post("/timers/pause_all")
        resp.raise_for_status()

    async def resume_all(self) -> None:
        resp = await self.client.post("/timers/resume_all")
        resp.raise_for_status()

    async def tick(self, seconds: float) -> None:
        resp = await self.client.post("/tick", params={"seconds": seconds})
        resp.raise_for_status()
