import os
import sys
import pytest
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from mytimer.core.timer_manager import TimerManager


def test_create_timer():
    tm = TimerManager()
    timer_id = tm.create_timer(10)
    assert timer_id in tm.timers
    assert tm.timers[timer_id].remaining == 10


def test_tick_and_finish():
    tm = TimerManager()
    timer_id = tm.create_timer(5)
    tm.tick(3)
    assert tm.timers[timer_id].remaining == 2
    assert not tm.timers[timer_id].finished
    tm.tick(5)
    assert tm.timers[timer_id].remaining == 0
    assert tm.timers[timer_id].finished


def test_pause_and_resume():
    tm = TimerManager()
    timer_id = tm.create_timer(10)
    tm.pause_timer(timer_id)
    tm.tick(5)
    # should not decrease while paused
    assert tm.timers[timer_id].remaining == 10
    tm.resume_timer(timer_id)
    tm.tick(4)
    assert tm.timers[timer_id].remaining == 6


def test_remove_timer():
    tm = TimerManager()
    timer_id = tm.create_timer(10)
    tm.remove_timer(timer_id)
    assert timer_id not in tm.timers



def test_zero_duration_timer_finishes_immediately():
    tm = TimerManager()
    timer_id = tm.create_timer(0)
    timer = tm.timers[timer_id]
    assert timer.finished
    assert not timer.running
    assert timer.remaining == 0

def test_create_timer_non_positive_duration():
    tm = TimerManager()
    tid_zero = tm.create_timer(0)
    zero_timer = tm.timers[tid_zero]
    assert zero_timer.remaining == 0
    assert zero_timer.finished

    tid_neg = tm.create_timer(-5)
    neg_timer = tm.timers[tid_neg]
    assert neg_timer.remaining == 0
    assert neg_timer.finished



def test_tick_negative_seconds():
    tm = TimerManager()
    tm.create_timer(5)
    with pytest.raises(ValueError):
        tm.tick(-1)

def test_tick_after_finish_no_change():
    tm = TimerManager()
    timer_id = tm.create_timer(1)
    tm.tick(1)
    assert tm.timers[timer_id].finished
    tm.tick(5)
    assert tm.timers[timer_id].remaining == 0
    assert tm.timers[timer_id].finished


def test_pause_resume_finished_timer_does_nothing():
    tm = TimerManager()
    timer_id = tm.create_timer(1)
    tm.tick(1)
    tm.pause_timer(timer_id)
    assert not tm.timers[timer_id].running
    tm.resume_timer(timer_id)
    assert not tm.timers[timer_id].running


def test_tick_zero_seconds():
    tm = TimerManager()
    timer_id = tm.create_timer(5)
    tm.tick(0)
    assert tm.timers[timer_id].remaining == 5


def test_batch_operations_and_reset(tmp_path):
    tm = TimerManager()
    ids = [tm.create_timer(5), tm.create_timer(3)]

    tm.pause_all()
    assert all(not tm.timers[i].running for i in ids)

    tm.resume_all()
    assert all(tm.timers[i].running for i in ids)

    tm.tick(2)
    tm.reset_all()
    assert all(
        tm.timers[i].remaining == tm.timers[i].duration and not tm.timers[i].finished
        for i in ids
    )

    tm.remove_all()
    assert not tm.timers


def test_save_and_load_state(tmp_path):
    path = tmp_path / "timers.json"
    tm = TimerManager()
    tid1 = tm.create_timer(5)
    tid2 = tm.create_timer(3)
    tm.pause_timer(tid1)
    tm.tick(1)
    tm.save_state(path)

    tm2 = TimerManager()
    tm2.load_state(path)
    assert tid1 in tm2.timers and tid2 in tm2.timers
    assert tm2.timers[tid1].remaining == 5
    assert not tm2.timers[tid1].running
    assert tm2.timers[tid2].remaining == 2


@pytest.mark.asyncio
async def test_auto_tick_background():
    tm = TimerManager()
    tid = tm.create_timer(0.1)
    await tm.start_auto_tick(0.02)
    await asyncio.sleep(0.15)
    await tm.stop_auto_tick()
    assert tm.timers[tid].finished


