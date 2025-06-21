"""Monitor timers and trigger notifications when they finish."""

from __future__ import annotations

import asyncio
import contextlib
from typing import Awaitable, Callable, Set

from timer_manager import TimerManager

NotifyCallback = Callable[[int], Awaitable[None]]


class Notifier:
    """Monitor a :class:`TimerManager` and invoke a callback on timer completion."""

    def __init__(self, manager: TimerManager, callback: NotifyCallback) -> None:
        self.manager = manager
        self.callback = callback
        self._task: asyncio.Task[None] | None = None
        self._interval = 1.0
        self._notified: Set[int] = set()
        self._running = False

    async def start(self, interval: float = 1.0) -> None:
        """Start monitoring timers."""
        if self._task:
            return
        self._interval = interval
        self._running = True
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        """Stop monitoring timers."""
        self._running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        self._task = None

    async def _run(self) -> None:
        while self._running:
            for tid, timer in list(self.manager.timers.items()):
                if timer.finished and tid not in self._notified:
                    await self.callback(tid)
                    self._notified.add(tid)
            await asyncio.sleep(self._interval)
