import os
import sys
import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from timer_manager import TimerManager


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

