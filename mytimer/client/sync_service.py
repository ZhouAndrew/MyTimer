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
import time
from pathlib import Path
import json as _json
import contextlib

from ..core.timer_manager import TimerManager

import httpx
import websockets


@dataclass
class TimerState:
    """Representation of a single timer's state."""

    duration: float
    remaining: float
    running: bool
    finished: bool
    created_at: float
    start_at: float | None

    def remaining_now(self) -> float:
        if self.running and self.start_at is not None:
            return max(0.0, self.duration - (time.time() - self.start_at))
        return self.remaining


class SyncService:
    """Maintain timer state synchronization via WebSocket or HTTP polling."""

    def __init__(
        self,
        base_url: str,
        reconnect_interval: float = 1.0,
        *,
        use_websocket: bool = True,
        storage_path: Path | None = None,
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
        self.local_mode = False
        self._storage_path = storage_path or Path.home() / ".timercli" / "timers.json"
        self._manager: TimerManager | None = None


    async def connect(self) -> None:
        """Start syncing timer state using WebSocket or HTTP polling."""
        if self._recv_task:
            return
        self._running = True
        try:
            if self.use_websocket:
                self._ws = await websockets.connect(self.ws_url)
                self.connected = True
                self._recv_task = asyncio.create_task(self._recv_loop())
            else:
                await self.client.get("/status")
                self._recv_task = asyncio.create_task(self._poll_loop())
            await self._fetch_state()
            self.local_mode = False
        except Exception:
            self.local_mode = True
            self.connected = False
            self._manager = TimerManager()
            self._manager.load_state(self._storage_path)
            self.state = {
                str(tid): TimerState(
                    duration=t.duration,
                    remaining=t.remaining,
                    running=t.running,
                    finished=t.finished,
                    created_at=t.created_at,
                    start_at=t.start_at,
                )
                for tid, t in self._manager.timers.items()
            }

    async def _fetch_state(self) -> None:
        resp = await self.client.get("/timers")
        resp.raise_for_status()
        data = resp.json()
        self.state = {
            str(tid): TimerState(
                duration=info["duration"],
                remaining=info.get("remaining", info["duration"]),
                running=info.get("running", info.get("start_at") is not None),
                finished=info.get("finished", False),
                created_at=info.get("created_at", time.time()),
                start_at=info.get("start_at"),
            )
            for tid, info in data.items()
        }

    def _handle_message(self, message: str) -> None:
        data = json.loads(message)
        if isinstance(data, dict) and "type" in data:
            if data.get("type") == "update":
                tid = str(data["timer_id"])
                state = self.state.get(tid)
                if state:
                    state.remaining = data.get("remaining", state.remaining)
                    state.running = data.get("running", state.running)
                    state.finished = data.get("finished", state.finished)
                    state.duration = data.get("duration", state.duration)
                    state.created_at = data.get("created_at", state.created_at)
                    state.start_at = data.get("start_at", state.start_at)
                else:
                    self.state[tid] = TimerState(
                        duration=data.get("duration", data.get("remaining", 0)),
                        remaining=data.get("remaining", 0),
                        running=data.get("running", data.get("start_at") is not None),
                        finished=data.get("finished", False),
                        created_at=data.get("created_at", time.time()),
                        start_at=data.get("start_at"),
                    )
        else:
            self.state = {
                str(tid): TimerState(
                    duration=info["duration"],
                    remaining=info.get("remaining", info["duration"]),
                    running=info.get("running", info.get("start_at") is not None),
                    finished=info.get("finished", False),
                    created_at=info.get("created_at", time.time()),
                    start_at=info.get("start_at"),
                )
                for tid, info in data.items()
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
                self.local_mode = True
                self.connected = False
                self._manager = TimerManager()
                self._manager.load_state(self._storage_path)
                self.state = {
                    str(tid): TimerState(
                        duration=t.duration,
                        remaining=t.remaining,
                        running=t.running,
                        finished=t.finished,
                        created_at=t.created_at,
                        start_at=t.start_at,
                    )
                    for tid, t in self._manager.timers.items()
                }
                return
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
                self.local_mode = True
                self.connected = False
                self._manager = TimerManager()
                self._manager.load_state(self._storage_path)
                self.state = {
                    str(tid): TimerState(
                        duration=t.duration,
                        remaining=t.remaining,
                        running=t.running,
                        finished=t.finished,
                        created_at=t.created_at,
                        start_at=t.start_at,
                    )
                    for tid, t in self._manager.timers.items()
                }
                return
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
        if self.local_mode and self._manager is not None:
            self._manager.save_state(self._storage_path)

    async def create_timer(self, duration: float) -> int:
        if self.local_mode and self._manager is not None:
            tid = self._manager.create_timer(duration)
            self._manager.save_state(self._storage_path)
            self.state[str(tid)] = TimerState(
                duration=duration,
                remaining=duration,
                running=True,
                finished=False,
                created_at=self._manager.timers[tid].created_at,
                start_at=self._manager.timers[tid].start_at,
            )
            return tid
        resp = await self.client.post("/timers", params={"duration": duration})
        resp.raise_for_status()
        return resp.json()["timer_id"]

    async def pause_timer(self, timer_id: int) -> None:
        if self.local_mode and self._manager is not None:
            self._manager.pause_timer(timer_id)
            self._manager.save_state(self._storage_path)
            t = self._manager.timers.get(timer_id)
            if t:
                self.state[str(timer_id)].running = False
                self.state[str(timer_id)].remaining = t.remaining
                self.state[str(timer_id)].start_at = None
                self.state[str(timer_id)].finished = t.finished
            return
        resp = await self.client.post(f"/timers/{timer_id}/pause")
        resp.raise_for_status()

    async def resume_timer(self, timer_id: int) -> None:
        if self.local_mode and self._manager is not None:
            self._manager.resume_timer(timer_id)
            self._manager.save_state(self._storage_path)
            t = self._manager.timers.get(timer_id)
            if t:
                self.state[str(timer_id)].running = True
                self.state[str(timer_id)].start_at = t.start_at
            return
        resp = await self.client.post(f"/timers/{timer_id}/resume")
        resp.raise_for_status()

    async def remove_timer(self, timer_id: int) -> None:
        if self.local_mode and self._manager is not None:
            self._manager.remove_timer(timer_id)
            self._manager.save_state(self._storage_path)
            self.state.pop(str(timer_id), None)
            return
        resp = await self.client.delete(f"/timers/{timer_id}")
        resp.raise_for_status()

    async def remove_all_timers(self) -> None:
        if self.local_mode and self._manager is not None:
            self._manager.remove_all()
            self._manager.save_state(self._storage_path)
            self.state.clear()
            return
        resp = await self.client.delete("/timers")
        resp.raise_for_status()

    async def pause_all(self) -> None:
        if self.local_mode and self._manager is not None:
            self._manager.pause_all()
            self._manager.save_state(self._storage_path)
            for t in self.state.values():
                t.running = False
                t.start_at = None
            return
        resp = await self.client.post("/timers/pause_all")
        resp.raise_for_status()

    async def resume_all(self) -> None:
        if self.local_mode and self._manager is not None:
            self._manager.resume_all()
            self._manager.save_state(self._storage_path)
            for tid, t in self._manager.timers.items():
                state = self.state.get(str(tid))
                if state:
                    state.running = True
                    state.start_at = t.start_at
            return
        resp = await self.client.post("/timers/resume_all")
        resp.raise_for_status()

    async def tick(self, seconds: float) -> None:
        if self.local_mode and self._manager is not None:
            self._manager.tick(seconds)
            self._manager.save_state(self._storage_path)
            for tid, t in self._manager.timers.items():
                state = self.state.get(str(tid))
                if state:
                    state.remaining = t.remaining
                    state.running = t.running
                    state.finished = t.finished
                    state.start_at = t.start_at
            return
        resp = await self.client.post("/tick", params={"seconds": seconds})
        resp.raise_for_status()
