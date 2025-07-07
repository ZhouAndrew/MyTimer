"""内部计时器数据结构与管理逻辑。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Callable, Awaitable, List
import asyncio
import contextlib
import json
from pathlib import Path


@dataclass
class Timer:
    """Simple countdown timer."""

    duration: float
    remaining: float
    running: bool = True
    finished: bool = False

    def __post_init__(self) -> None:
        if self.duration <= 0:
            self.remaining = 0
            self.running = False
            self.finished = True

    def tick(self, seconds: float) -> None:
        """Advance the timer by ``seconds`` if running.

        Raises
        ------
        ValueError
            If ``seconds`` is negative.
        """
        if seconds < 0:
            raise ValueError("seconds must be non-negative")

        if self.running and not self.finished:
            self.remaining -= seconds
            if self.remaining <= 0:
                self.remaining = 0
                self.finished = True
                self.running = False


class TimerManager:
    """Manage multiple :class:`Timer` instances."""
    def __init__(self) -> None:
        """Initialize the manager with an empty timer registry."""
        self.timers: Dict[int, Timer] = {}
        self._next_id = 1
        self._tick_callbacks: List[Callable[[int, Timer], Awaitable[None] | None]] = []
        self._finish_callbacks: List[Callable[[int, Timer], Awaitable[None] | None]] = []
        self._auto_task: asyncio.Task[None] | None = None
        self._auto_interval = 1.0
        self._auto_running = False

    def register_on_tick(self, callback: Callable[[int, Timer], Awaitable[None] | None]) -> None:
        """Register a callback triggered after each timer ``tick``."""
        self._tick_callbacks.append(callback)

    def register_on_finish(self, callback: Callable[[int, Timer], Awaitable[None] | None]) -> None:
        """Register a callback when a timer reaches zero."""
        self._finish_callbacks.append(callback)

    def create_timer(self, duration: float) -> int:
        """Create a new timer and return its identifier.

        A duration less than or equal to zero will create a timer that is
        immediately finished. This mirrors the behaviour of ticking a timer
        down to zero but avoids exposing negative remaining times.
        """

        timer_id = self._next_id
        self._next_id += 1

        if duration <= 0:
            timer = Timer(duration=duration, remaining=0, running=False, finished=True)
        else:
            timer = Timer(duration=duration, remaining=duration)

        self.timers[timer_id] = timer
        return timer_id

    def tick(self, seconds: float) -> None:
        """Advance all managed timers.

        Raises
        ------
        ValueError
            If ``seconds`` is negative.
        """
        if seconds < 0:
            raise ValueError("seconds must be non-negative")

        for tid, timer in list(self.timers.items()):
            was_finished = timer.finished
            timer.tick(seconds)
            self._run_callbacks(self._tick_callbacks, tid, timer)
            if not was_finished and timer.finished:
                self._run_callbacks(self._finish_callbacks, tid, timer)

    def pause_timer(self, timer_id: int) -> None:
        """Pause the specified timer."""
        timer = self.timers.get(timer_id)
        if timer and not timer.finished:
            timer.running = False

    def resume_timer(self, timer_id: int) -> None:
        """Resume a paused timer."""
        timer = self.timers.get(timer_id)
        if timer and not timer.finished:
            timer.running = True

    def remove_timer(self, timer_id: int) -> None:
        """Remove a timer from the registry."""
        self.timers.pop(timer_id, None)

    def _run_callbacks(self, cbs: List[Callable[[int, Timer], Awaitable[None] | None]], tid: int, timer: Timer) -> None:
        """Invoke callbacks with ``tid`` and ``timer`` safely."""
        for cb in cbs:
            if asyncio.iscoroutinefunction(cb):
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(cb(tid, timer))
                except RuntimeError:
                    asyncio.run(cb(tid, timer))
            else:
                cb(tid, timer)

    def reset_timer(self, timer_id: int) -> None:
        """Reset a timer back to its original duration and running state."""
        timer = self.timers.get(timer_id)
        if timer:
            timer.remaining = timer.duration
            timer.running = True
            timer.finished = False

    def pause_all(self) -> None:
        """Pause all running timers."""
        for timer in self.timers.values():
            if not timer.finished:
                timer.running = False

    def resume_all(self) -> None:
        """Resume all non-finished timers."""
        for timer in self.timers.values():
            if not timer.finished:
                timer.running = True

    def remove_all(self) -> None:
        """Remove all timers from the manager."""
        self.timers.clear()

    def reset_all(self) -> None:
        """Reset every timer to its initial state."""
        for tid in list(self.timers.keys()):
            self.reset_timer(tid)

    def save_state(self, path: str | Path) -> None:
        """Persist current timers to a JSON file."""
        file_path = Path(path)
        data = {
            "next_id": self._next_id,
            "timers": {
                str(tid): {
                    "duration": t.duration,
                    "remaining": t.remaining,
                    "running": t.running,
                    "finished": t.finished,
                }
                for tid, t in self.timers.items()
            },
        }
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(data, f)

    def load_state(self, path: str | Path) -> None:
        """Load timers from a JSON file if it exists."""
        file_path = Path(path)
        if not file_path.exists():
            return
        try:
            with file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return

        self.timers.clear()
        timers_data = data.get("timers", {})
        for tid_str, tdata in timers_data.items():
            tid = int(tid_str)
            timer = Timer(
                duration=tdata.get("duration", 0),
                remaining=tdata.get("remaining", 0),
                running=tdata.get("running", True),
                finished=tdata.get("finished", False),
            )
            self.timers[tid] = timer
        self._next_id = data.get("next_id", max(self.timers.keys(), default=0) + 1)

    async def _auto_loop(self) -> None:
        while self._auto_running:
            self.tick(self._auto_interval)
            await asyncio.sleep(self._auto_interval)

    async def start_auto_tick(self, interval: float = 1.0) -> None:
        """Start background ticking at ``interval`` seconds."""
        if self._auto_task:
            return
        if interval <= 0:
            return
        self._auto_interval = interval
        self._auto_running = True
        self._auto_task = asyncio.create_task(self._auto_loop())

    async def stop_auto_tick(self) -> None:
        """Stop the background ticking task."""
        self._auto_running = False
        if self._auto_task:
            self._auto_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._auto_task
        self._auto_task = None
