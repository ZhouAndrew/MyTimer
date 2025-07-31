import subprocess
import time
import requests
import pytest

from qt_client.network_client import NetworkClient


@pytest.fixture(scope="module", autouse=True)
def start_api():
    proc = subprocess.Popen([
        "uvicorn",
        "mytimer.server.api:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8011",
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for _ in range(10):
        try:
            requests.get("http://127.0.0.1:8011/timers", timeout=1)
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


def test_network_client_flow(start_api):
    client = NetworkClient("http://127.0.0.1:8011")
    tid = client.create_timer(2)
    data = client.list_timers()
    assert str(tid) in data
    client.pause_timer(tid)
    client.resume_timer(tid)
    data = client.list_timers()
    assert data[str(tid)]["duration"] == 2

