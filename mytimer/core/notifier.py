"""Monitor timers and trigger notifications when they finish."""

from __future__ import annotations

import asyncio
import contextlib
from typing import Awaitable, Callable, Set
import shutil
import subprocess
import sys

from .timer_manager import TimerManager

NotifyCallback = Callable[[int], Awaitable[None]]


class Notifier:
    """Monitor a :class:`TimerManager` and invoke a callback on timer completion.

    Parameters
    ----------
    manager:
        The :class:`TimerManager` instance to observe.
    callback:
        Optional coroutine/function invoked when a timer finishes. If not
        provided, a notification will be emitted according to ``mode``.
    mode:
        Notification mode: ``"print"`` (default) prints a message, ``"silent"``
        suppresses all output and ``"system"`` attempts to use the OS
        notification service.
    """

    def __init__(
        self,
        manager: TimerManager,
        callback: NotifyCallback | None = None,
        *,
        mode: str = "print",
    ) -> None:
        self.manager = manager
        self.callback = callback
        self.mode = mode
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
                    await self._notify(tid)
                    self._notified.add(tid)
            await asyncio.sleep(self._interval)

    async def _notify(self, timer_id: int) -> None:
        message = f"Timer {timer_id} finished!"
        if self.callback:
            result = self.callback(timer_id)
            if asyncio.iscoroutine(result):
                await result
            return
        if self.mode == "silent":
            return
        if self.mode in {"print", "system"}:
            print(message)
        if self.mode == "system":
            self._system_notify(message)

    def _system_notify(self, message: str) -> None:
        try:
            if shutil.which("notify-send"):
                subprocess.run(["notify-send", message], check=False)
            elif sys.platform == "darwin":
                subprocess.run(
                    [
                        "osascript",
                        "-e",
                        f'display notification "{message}" with title "MyTimer"',
                    ],
                    check=False,
                )
        except Exception:
            pass
