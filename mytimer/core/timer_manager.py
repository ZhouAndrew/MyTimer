"""内部计时器数据结构与管理逻辑。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


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
        for timer in list(self.timers.values()):
            timer.tick(seconds)

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
