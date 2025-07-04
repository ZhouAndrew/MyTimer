from __future__ import annotations

"""Background task that automatically ticks timers at a fixed interval."""

import asyncio
import contextlib
import os
from typing import Optional

from ..core.timer_manager import TimerManager


class AutoTicker:
    """Periodically call :meth:`TimerManager.tick`."""

    def __init__(self, manager: TimerManager, interval: float = 1.0) -> None:
        self.manager = manager
        self.interval = interval
        self._task: Optional[asyncio.Task[None]] = None
        self._running = False

    async def start(self, interval: Optional[float] = None) -> None:
        """Start ticking timers in the background."""
        if interval is not None:
            self.interval = interval
        if self._task or self.interval <= 0:
            return
        self._running = True
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        """Stop the background ticking task."""
        self._running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        self._task = None

    async def _run(self) -> None:
        while self._running:
            self.manager.tick(self.interval)
            await asyncio.sleep(self.interval)


def create_auto_ticker(manager: TimerManager) -> AutoTicker:
    """Factory creating :class:`AutoTicker` based on environment config."""
    interval = float(os.environ.get("MYTIMER_AUTO_TICK_INTERVAL", "0"))
    return AutoTicker(manager, interval=interval if interval > 0 else 0)
