import asyncio
import time
import subprocess
import pytest

from mytimer.client.sync_service import SyncService


@pytest.fixture(scope="module", autouse=True)
def start_server():
    proc = subprocess.Popen([
        "uvicorn",
        "mytimer.server.api:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8002",
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # wait for startup
    for _ in range(10):
        try:
            import requests

            requests.get("http://127.0.0.1:8002/timers", timeout=1)
            break
        except Exception:
            time.sleep(0.5)
    else:
        proc.terminate()
        proc.wait()
        raise RuntimeError("API server failed to start")
    yield
    proc.terminate()
    proc.wait()


@pytest.mark.asyncio
async def test_sync_flow(start_server):
    svc = SyncService("http://127.0.0.1:8002")
    await svc.connect()

    timer_id = await svc.create_timer(5)
    # wait for websocket state update
    for _ in range(10):
        if str(timer_id) in svc.state:
            break
        await asyncio.sleep(0.1)
    assert str(timer_id) in svc.state
    assert svc.state[str(timer_id)].remaining == 5

    await svc.tick(2)
    await asyncio.sleep(0.1)
    assert svc.state[str(timer_id)].remaining == 3

    await svc.pause_timer(timer_id)
    await svc.tick(1)
    await asyncio.sleep(0.1)
    assert svc.state[str(timer_id)].remaining == 3

    await svc.resume_timer(timer_id)
    await svc.tick(1)
    await asyncio.sleep(0.1)
    assert svc.state[str(timer_id)].remaining == 2

    await svc.remove_timer(timer_id)
    await asyncio.sleep(0.1)
    assert str(timer_id) not in svc.state

    await svc.close()
