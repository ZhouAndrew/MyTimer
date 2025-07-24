import subprocess
import sys
import time
import requests
import pytest

PORT = 8009
BASE_URL = f"http://127.0.0.1:{PORT}"

@pytest.fixture(scope="module", autouse=True)
def start_server():
    proc = subprocess.Popen([
        "uvicorn",
        "mytimer.server.api:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(PORT),
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for _ in range(10):
        try:
            requests.get(f"{BASE_URL}/timers", timeout=1)
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

def test_tui_full_lifecycle(start_server):
    data = requests.get(f"{BASE_URL}/timers", timeout=5).json()
    for tid in list(data.keys()):
        requests.delete(f"{BASE_URL}/timers/{tid}", timeout=5)

    proc = subprocess.Popen(
        [sys.executable, "-m", "mytimer.client.tui_app", "--url", BASE_URL],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    time.sleep(1)
    cmds = "c\n5\nTest\ns\np\nr\nd\ny\nq\n"
    stdout, stderr = proc.communicate(cmds, timeout=20)
    assert proc.returncode == 0, stderr
    data = requests.get(f"{BASE_URL}/timers", timeout=5).json()
    assert data == {}
