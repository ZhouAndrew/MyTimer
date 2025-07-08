import asyncio
import os
import sys
import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from mytimer.core.timer_manager import TimerManager
from mytimer.core.notifier import Notifier


@pytest.mark.asyncio
async def test_notifier_triggers_on_finish():
    tm = TimerManager()
    timer_id = tm.create_timer(5)

    received: list[int] = []

    async def on_notify(tid: int) -> None:
        received.append(tid)

    notifier = Notifier(tm, on_notify)
    await notifier.start(interval=0.01)

    tm.tick(5)
    await asyncio.sleep(0.05)
    await notifier.stop()

    assert timer_id in received


@pytest.mark.asyncio
async def test_notifier_only_once():
    tm = TimerManager()
    timer_id = tm.create_timer(2)

    count = 0

    async def on_notify(tid: int) -> None:
        nonlocal count
        count += 1

    notifier = Notifier(tm, on_notify)
    await notifier.start(interval=0.01)

    tm.tick(2)
    await asyncio.sleep(0.03)
    tm.tick(1)
    await asyncio.sleep(0.03)
    await notifier.stop()

    assert count == 1 and timer_id in tm.timers


@pytest.mark.asyncio
async def test_notifier_silent_mode(capsys):
    tm = TimerManager()
    tid = tm.create_timer(1)

    notifier = Notifier(tm, None, mode="silent")
    await notifier.start(interval=0.01)

    tm.tick(1)
    await asyncio.sleep(0.05)
    await notifier.stop()

    captured = capsys.readouterr()
    assert captured.out == ""
