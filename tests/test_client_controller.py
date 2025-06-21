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
        "api_server:app",
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


def run_cli(*args: str) -> str:
    cmd = [sys.executable, "client_controller.py", "--url", "http://127.0.0.1:8003", *args]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def test_cli_flow(start_server):
    tid = int(run_cli("create", "5"))
    data = json.loads(run_cli("list"))
    assert str(tid) in data

    run_cli("pause", str(tid))
    run_cli("tick", "2")
    data = json.loads(run_cli("list"))
    assert data[str(tid)]["remaining"] == 5

    run_cli("resume", str(tid))
    run_cli("tick", "3")
    data = json.loads(run_cli("list"))
    assert data[str(tid)]["remaining"] == 2

    run_cli("remove", str(tid))
    data = json.loads(run_cli("list"))
    assert str(tid) not in data


def test_interactive_quit(start_server):
    proc = subprocess.Popen(
        [sys.executable, "client_controller.py", "--url", "http://127.0.0.1:8003", "interactive"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    proc.stdin.write("quit\n")
    proc.stdin.flush()
    stdout, stderr = proc.communicate(timeout=5)
    assert proc.returncode == 0
