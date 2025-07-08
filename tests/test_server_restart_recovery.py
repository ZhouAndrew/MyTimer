import os
import subprocess
import time
import requests
import pytest


def start_server(port: int, state_file: str):
    env = os.environ.copy()
    env["MYTIMER_API_PORT"] = str(port)
    env["MYTIMER_STATE_FILE"] = state_file
    proc = subprocess.Popen(
        [
            "uvicorn",
            "mytimer.server.api:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    for _ in range(10):
        try:
            requests.get(f"http://127.0.0.1:{port}/timers", timeout=1)
            break
        except Exception:
            time.sleep(0.5)
    else:
        proc.terminate()
        proc.wait()
        raise RuntimeError("API server failed to start")
    return proc


def test_restart_recovers_state(tmp_path):
    port = 8008
    state = tmp_path / "state.json"

    proc = start_server(port, str(state))
    try:
        requests.post(
            f"http://127.0.0.1:{port}/timers", params={"duration": 5}, timeout=5
        )
        requests.post(f"http://127.0.0.1:{port}/tick", params={"seconds": 2}, timeout=5)
    finally:
        proc.terminate()
        proc.wait()

    proc = start_server(port, str(state))
    try:
        resp = requests.get(f"http://127.0.0.1:{port}/timers", timeout=5)
        data = resp.json()
        assert "1" in data and data["1"]["remaining"] == 3
    finally:
        proc.terminate()
        proc.wait()
