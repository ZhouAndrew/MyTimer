"""Terminal notifier for timer completions."""

from __future__ import annotations

import asyncio
import contextlib
import shutil
import subprocess
import sys
from typing import Callable, Awaitable, Set

from rich.console import Console
from rich.panel import Panel

from timer_manager import TimerManager

NotifyFunc = Callable[[int, str], Awaitable[None]] | Callable[[int, str], None]


class TUINotifier:
    """Display timer completion notifications in the terminal and via the OS."""

    def __init__(
        self,
        manager: TimerManager,
        *,
        interval: float = 1.0,
        use_system: bool = True,
        callback: NotifyFunc | None = None,
    ) -> None:
        self.manager = manager
        self.interval = interval
        self.use_system = use_system
        self.callback = callback
        self.console = Console()
        self._task: asyncio.Task[None] | None = None
        self._notified: Set[int] = set()
        self._running = False

    async def start(self) -> None:
        if self._task:
            return
        self._running = True
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
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
            await asyncio.sleep(self.interval)

    async def _notify(self, timer_id: int) -> None:
        message = f"Timer {timer_id} finished!"
        if self.callback:
            result = self.callback(timer_id, message)
            if asyncio.iscoroutine(result):
                await result
        else:
            self.console.print(Panel(message, title="Notification"))
            if self.use_system:
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
