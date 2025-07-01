"""内部计时器数据结构与管理逻辑。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Callable, Awaitable, List
import asyncio


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
