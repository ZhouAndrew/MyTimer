import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from mytimer.core.timer_manager import TimerManager


def test_start_at_updates_on_pause_resume(monkeypatch):
    fake_times = [100.0, 101.0, 102.0, 103.0]

    def fake_time():
        return fake_times.pop(0)

    monkeypatch.setattr("mytimer.core.timer_manager.time.time", fake_time)
    tm = TimerManager()
    tid = tm.create_timer(5)
    original = tm.timers[tid].start_at
    tm.pause_timer(tid)
    assert tm.timers[tid].start_at is None
    tm.resume_timer(tid)
    assert tm.timers[tid].start_at > original
