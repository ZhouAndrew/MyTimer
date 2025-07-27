import json
import subprocess
import sys
import time
import json

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
        "8004",
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for _ in range(10):
        try:
            requests.get("http://127.0.0.1:8004/timers", timeout=1)
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


def test_input_handler_flow(start_server):
    cmds = "\n".join([
        "create 5",
        "pause 1",
        "tick 2",
        "resume 1",
        "tick 2",
        "list",
        "remove 1",
        "quit",
        "",  # ensure newline at end
    ])
    proc = subprocess.Popen(
        [sys.executable, "-m", "mytimer.client.input_handler", "--url", "http://127.0.0.1:8004"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    stdout, stderr = proc.communicate(cmds, timeout=15)
    assert proc.returncode == 0, stderr
    lines = [l for l in stdout.splitlines() if l.strip()]
    timer_id = int(lines[0])
    state = json.loads(lines[5])  # after "list" command output (6th output)
    assert str(timer_id) in state
    assert state[str(timer_id)]["remaining"] == pytest.approx(3, rel=0.02, abs=0.1)
    data = requests.get("http://127.0.0.1:8004/timers", timeout=5).json()
    assert str(timer_id) not in data


def test_input_handler_all_commands(start_server):
    cmds = "\n".join([
        "create 3",
        "create 4",
        "pause all",
        "resume all",
        "remove all",
        "list",
        "create 2",
        "clear",
        "list",
        "quit",
        "",
    ])
    proc = subprocess.Popen(
        [sys.executable, "-m", "mytimer.client.input_handler", "--url", "http://127.0.0.1:8004"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    stdout, stderr = proc.communicate(cmds, timeout=20)
    assert proc.returncode == 0, stderr
    lines = [l for l in stdout.splitlines() if l.strip()]
    # outputs: id1, id2, paused all, resumed all, removed all, {}, id3, removed all, {}, ...
    state_after_remove = json.loads(lines[5])
    assert state_after_remove == {}
    state_after_clear = json.loads(lines[8])
    assert state_after_clear == {}


def test_input_handler_suggestion(start_server):
    proc = subprocess.Popen(
        [sys.executable, "-m", "mytimer.client.input_handler", "--url", "http://127.0.0.1:8004"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    stdout, stderr = proc.communicate("creat\nquit\n", timeout=10)
    assert proc.returncode == 0, stderr
    assert "Did you mean 'create'" in stdout
