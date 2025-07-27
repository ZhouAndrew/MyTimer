import asyncio
import subprocess
import time
import requests
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
        "8007",
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for _ in range(10):
        try:
            requests.get("http://127.0.0.1:8007/timers", timeout=1)
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
async def test_two_clients_receive_updates(start_server):
    svc1 = SyncService("http://127.0.0.1:8007")
    svc2 = SyncService("http://127.0.0.1:8007")
    await svc1.connect()
    await svc2.connect()

    tid = await svc1.create_timer(4)
    for _ in range(20):
        if str(tid) in svc1.state and str(tid) in svc2.state:
            break
        await asyncio.sleep(0.1)
    assert str(tid) in svc1.state and str(tid) in svc2.state

    await svc1.tick(1)
    for _ in range(20):
        if svc1.state[str(tid)].remaining == 3 and svc2.state[str(tid)].remaining == 3:
            break
        await asyncio.sleep(0.1)
    assert svc1.state[str(tid)].remaining == pytest.approx(3, rel=0.02, abs=0.1)
    assert svc2.state[str(tid)].remaining == pytest.approx(3, rel=0.02, abs=0.1)

    await svc2.remove_timer(tid)
    for _ in range(20):
        if str(tid) not in svc1.state and str(tid) not in svc2.state:
            break
        await asyncio.sleep(0.1)
    assert str(tid) not in svc1.state and str(tid) not in svc2.state

    await svc1.close()
    await svc2.close()
