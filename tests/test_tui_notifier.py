import asyncio
import os
import sys
import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from timer_manager import TimerManager
from tui_notifier import TUINotifier


@pytest.mark.asyncio
async def test_tui_notifier_triggers_callback():
    tm = TimerManager()
    tid = tm.create_timer(2)
    received: list[int] = []

    async def cb(timer_id: int, message: str) -> None:
        received.append(timer_id)

    notifier = TUINotifier(tm, interval=0.01, use_system=False, callback=cb)
    await notifier.start()
    tm.tick(2)
    await asyncio.sleep(0.05)
    await notifier.stop()

    assert received == [tid]


@pytest.mark.asyncio
async def test_tui_notifier_only_once():
    tm = TimerManager()
    tid = tm.create_timer(1)
    count = 0

    def cb(timer_id: int, message: str) -> None:
        nonlocal count
        count += 1

    notifier = TUINotifier(tm, interval=0.01, use_system=False, callback=cb)
    await notifier.start()
    tm.tick(1)
    await asyncio.sleep(0.05)
    tm.tick(1)
    await asyncio.sleep(0.05)
    await notifier.stop()

    assert count == 1
    assert tid in tm.timers
