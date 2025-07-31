"""内部计时器数据结构与管理逻辑。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Callable, Awaitable, List
import asyncio
import contextlib
import json
import time
from pathlib import Path


@dataclass
class Timer:
    """Simple countdown timer using timestamp-based progress."""

    duration: float
    remaining: float
    running: bool = True
    finished: bool = False
    created_at: float = field(default_factory=time.time)
    start_at: float | None = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if self.duration <= 0:
            self.remaining = 0
            self.running = False
            self.finished = True
            self.start_at = None
        elif not self.running:
            self.start_at = None

    def remaining_now(self) -> float:
        """Return the current remaining time."""
        return self.remaining

    def tick(self, seconds: float) -> None:
        """Simulate elapsing ``seconds`` of time for compatibility."""
        if seconds < 0:
            raise ValueError("seconds must be non-negative")
        if self.running and not self.finished:
            self.remaining = max(0.0, self.remaining - seconds)
        if self.running and self.remaining_now() <= 0:
            self.remaining = 0
            self.finished = True
            self.running = False
            self.start_at = None
                

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

        now = time.time()
        if duration <= 0:
            timer = Timer(
                duration=duration,
                remaining=0,
                running=False,
                finished=True,
                created_at=now,
                start_at=None,
            )
        else:
            timer = Timer(
                duration=duration,
                remaining=duration,
                created_at=now,
                start_at=now,
            )

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
        if timer and not timer.finished and timer.running:
            timer.remaining = timer.remaining_now()
            timer.running = False
            timer.start_at = None

    def resume_timer(self, timer_id: int) -> None:
        """Resume a paused timer."""
        timer = self.timers.get(timer_id)
        if timer and not timer.finished and not timer.running:
            timer.running = True
            timer.start_at = time.time()

    def remove_timer(self, timer_id: int) -> None:
        """Remove a timer from the registry."""
        self.timers.pop(timer_id, None)

    def pause_all(self) -> None:
        """Pause all running timers."""
        for timer in self.timers.values():
            if not timer.finished and timer.running:
                timer.remaining = timer.remaining_now()
                timer.running = False
                timer.start_at = None
                
    def resume_all(self) -> None:
        """Resume all non-finished timers."""
        for timer in self.timers.values():
            if not timer.finished and not timer.running:
                timer.running = True
                timer.start_at = time.time()

    def remove_all(self) -> None:
        """Remove all timers from the manager."""
        self.timers.clear()

    def reset_all(self) -> None:
        """Reset all timers to their initial duration and resume them."""
        for timer in self.timers.values():
            timer.remaining = timer.duration
            timer.running = True
            timer.finished = False
            timer.start_at = time.time()

    def running_count(self) -> int:
        """Return the number of running timers."""
        return sum(1 for t in self.timers.values() if t.running and not t.finished)

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
            timer.start_at = time.time()


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
                    "created_at": t.created_at,
                    "start_at": t.start_at,
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
                created_at=tdata.get("created_at", time.time()),
                start_at=tdata.get("start_at"),
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
