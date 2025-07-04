import subprocess
import time
import os
import asyncio
import requests
import pytest

from mytimer.client.sync_service import SyncService


@pytest.fixture(scope="module", autouse=True)
def start_server():
    env = os.environ.copy()
    env["MYTIMER_AUTO_TICK_INTERVAL"] = "0.05"
    proc = subprocess.Popen([
        "uvicorn",
        "mytimer.server.api:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8006",
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    for _ in range(10):
        try:
            requests.get("http://127.0.0.1:8006/timers", timeout=1)
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
async def test_auto_tick_updates_client(start_server):
    svc = SyncService("http://127.0.0.1:8006")
    await svc.connect()
    tid = await svc.create_timer(0.15)
    for _ in range(20):
        state = svc.state.get(str(tid))
        if state and state.finished:
            break
        await asyncio.sleep(0.05)
    await svc.close()
    assert str(tid) in svc.state and svc.state[str(tid)].finished

