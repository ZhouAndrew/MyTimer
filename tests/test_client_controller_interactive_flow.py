import json
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
        "8005",
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for _ in range(10):
        try:
            requests.get("http://127.0.0.1:8005/timers", timeout=1)
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


def test_interactive_flow(start_server):
    cmds = "\n".join([
        "create 5",
        "pause 1",
        "tick 2",
        "resume 1",
        "tick 2",
        "list",
        "remove 1",
        "quit",
        "",
    ])
    proc = subprocess.Popen(
        [sys.executable, "-m", "mytimer.client.controller", "--url", "http://127.0.0.1:8005", "interactive"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    stdout, stderr = proc.communicate(cmds, timeout=15)
    assert proc.returncode == 0, stderr
    lines = [l.replace(">> ", "").strip() for l in stdout.splitlines() if l.strip() and l.strip() != ">>"]
    if lines[0].startswith("Type 'help'"):
        lines = lines[1:]
    timer_id = int(lines[0])
    state = json.loads(lines[5])
    assert str(timer_id) in state
    assert state[str(timer_id)]["remaining"] == pytest.approx(3, rel=0.02, abs=0.1)
    data = requests.get("http://127.0.0.1:8005/timers", timeout=5).json()
    assert str(timer_id) not in data
