import json
import os
import subprocess
import sys
import time

import pytest
import requests

PORT = 8011
BASE_URL = f"http://127.0.0.1:{PORT}"


def run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "mytimer.client.controller", "--url", BASE_URL, *args],
        capture_output=True,
        text=True,
    )


@pytest.fixture(scope="module", autouse=True)
def start_server():
    env = os.environ.copy()
    env["MYTIMER_AUTO_TICK_INTERVAL"] = "0.05"
    proc = subprocess.Popen(
        ["uvicorn", "mytimer.server.api:app", "--host", "127.0.0.1", "--port", str(PORT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
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


def test_tick_usage(start_server):
    result = run_cli("tick")
    assert result.returncode == 0
    assert "Usage: tick <seconds>" in result.stdout


def test_tick_advances_timer(start_server):
    tid = int(run_cli("create", "5").stdout.strip())
    run_cli("tick", "3")
    data = json.loads(run_cli("list").stdout.strip())
    remaining = data[str(tid)]["remaining"]
    assert 1.3 <= remaining <= 2.1


def test_tui_clears_screen(start_server):
    proc = subprocess.Popen(
        [sys.executable, "-m", "mytimer.client.tui_app", "--url", BASE_URL],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    stdout, _ = proc.communicate("q\n", timeout=5)
    assert proc.returncode == 0
    assert "\x1b[2J" in stdout or "\x1b[3J" in stdout


def test_timer_auto_decrease(start_server):
    tid = int(run_cli("create", "0.2").stdout.strip())
    time.sleep(0.4)
    data = json.loads(run_cli("list").stdout.strip())
    assert data[str(tid)]["finished"]


def test_cli_tui_consistency(start_server):
    tid = int(run_cli("create", "4").stdout.strip())
    run_cli("tick", "1")
    result = subprocess.run(
        [sys.executable, "-m", "mytimer.client.tui_app", "--url", BASE_URL, "--once"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    for line in result.stdout.splitlines():
        if f"Timer {tid}" in line:
            parts = [p.strip() for p in line.split("│") if p.strip()]
            remaining = float(parts[3])
            assert 1.0 <= remaining <= 3.1
            break
    else:
        pytest.fail("Timer row not found in TUI output")

