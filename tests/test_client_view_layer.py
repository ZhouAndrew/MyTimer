import subprocess
import sys
import time
import requests
import pytest


@pytest.fixture(scope="module", autouse=True)
def start_server():
    proc = subprocess.Popen([
        "uvicorn",
        "mytimer.server.api:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8003",
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for _ in range(10):
        try:
            requests.get("http://127.0.0.1:8003/timers", timeout=1)
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


def test_client_view_once(start_server):
    resp = requests.post("http://127.0.0.1:8003/timers", params={"duration": 5}, timeout=5)
    timer_id = resp.json()["timer_id"]

    result = subprocess.run(
        [sys.executable, "-m", "mytimer.client.view_layer", "--once", "--url", "http://127.0.0.1:8003"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert str(timer_id) in result.stdout
    assert "Running:" in result.stdout
