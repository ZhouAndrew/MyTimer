from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class Timer:
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
        if self.running and not self.finished:
            self.remaining -= seconds
            if self.remaining <= 0:
                self.remaining = 0
                self.finished = True
                self.running = False


class TimerManager:
    def __init__(self) -> None:
        self.timers: Dict[int, Timer] = {}
        self._next_id = 1

    def create_timer(self, duration: float) -> int:
        timer_id = self._next_id
        self._next_id += 1
        self.timers[timer_id] = Timer(duration=duration, remaining=duration)
        return timer_id

    def tick(self, seconds: float) -> None:
        for timer in list(self.timers.values()):
            timer.tick(seconds)

    def pause_timer(self, timer_id: int) -> None:
        timer = self.timers.get(timer_id)
        if timer and not timer.finished:
            timer.running = False

    def resume_timer(self, timer_id: int) -> None:
        timer = self.timers.get(timer_id)
        if timer and not timer.finished:
            timer.running = True

    def remove_timer(self, timer_id: int) -> None:
        self.timers.pop(timer_id, None)
