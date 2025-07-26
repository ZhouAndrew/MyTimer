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
    assert svc.state[str(timer_id)].remaining == pytest.approx(5, rel=0.01, abs=0.05)

    await svc.tick(2)
    await asyncio.sleep(0.1)
    assert svc.state[str(timer_id)].remaining == pytest.approx(3, rel=0.05, abs=0.5)

    await svc.pause_timer(timer_id)
    await svc.tick(1)
    await asyncio.sleep(0.1)
    assert svc.state[str(timer_id)].remaining == pytest.approx(3, rel=0.05, abs=0.5)

    await svc.resume_timer(timer_id)
    await svc.tick(1)
    await asyncio.sleep(0.1)
    assert svc.state[str(timer_id)].remaining == pytest.approx(2, abs=1.0)

    await svc.remove_timer(timer_id)
    await asyncio.sleep(0.1)
    assert str(timer_id) not in svc.state

    await svc.close()


@pytest.mark.asyncio
async def test_multi_client_sync(start_server):
    c1 = SyncService("http://127.0.0.1:8002")
    c2 = SyncService("http://127.0.0.1:8002")
    await c1.connect()
    await c2.connect()

    tid = await c1.create_timer(4)
    for _ in range(20):
        if str(tid) in c2.state:
            break
        await asyncio.sleep(0.1)
    assert str(tid) in c2.state

    await c2.tick(1)
    await asyncio.sleep(0.2)
    assert c1.state[str(tid)].remaining == pytest.approx(3, rel=0.05, abs=0.5)

    await c1.remove_timer(tid)
    await asyncio.sleep(0.2)
    assert str(tid) not in c1.state
    assert str(tid) not in c2.state

    await c1.close()
    await c2.close()


@pytest.mark.asyncio
async def test_reconnect_resync(start_server):
    svc = SyncService("http://127.0.0.1:8002", reconnect_interval=0.1)
    await svc.connect()

    tid = await svc.create_timer(5)
    for _ in range(20):
        if str(tid) in svc.state:
            break
        await asyncio.sleep(0.1)
    assert str(tid) in svc.state

    # force close connection to trigger reconnect
    await svc._ws.close()
    await asyncio.sleep(0.2)

    await svc.tick(1)
    for _ in range(20):
        state = svc.state.get(str(tid))
        if state and state.remaining == 4:
            break
        await asyncio.sleep(0.1)

    assert svc.state[str(tid)].remaining == pytest.approx(4, rel=0.05, abs=0.5)

    await svc.close()
