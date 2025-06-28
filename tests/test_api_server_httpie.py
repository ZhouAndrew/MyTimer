import subprocess
import json
import time
import os
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
        "8001",
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # Wait for the server to start
    for _ in range(10):
        try:
            requests.get("http://127.0.0.1:8001/timers", timeout=1)
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


def run_httpie(method, url, *args):
    env = os.environ.copy()
    env["NO_COLOR"] = "1"  # avoid ANSI color codes
    # Disable update checks which attempt network access
    temp_dir = os.path.join(os.getcwd(), "httpie_config")
    os.makedirs(temp_dir, exist_ok=True)
    with open(os.path.join(temp_dir, "config.json"), "w") as f:
        json.dump({"disable_update_warnings": True}, f)
    env["HTTPIE_CONFIG_DIR"] = temp_dir
    cmd = [
        "http",
        "--timeout=5",
        "--print=b",
        method,
        url,
        *args,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_httpie_flow(start_server):
    # create timer
    data = run_httpie("POST", "http://127.0.0.1:8001/timers", "duration==5")
    timer_id = data["timer_id"]

    data = run_httpie("GET", "http://127.0.0.1:8001/timers")
    assert str(timer_id) in data
    assert data[str(timer_id)]["remaining"] == 5

    run_httpie("POST", f"http://127.0.0.1:8001/timers/{timer_id}/pause")
    run_httpie("POST", "http://127.0.0.1:8001/tick", "seconds==2")
    data = run_httpie("GET", "http://127.0.0.1:8001/timers")
    assert data[str(timer_id)]["remaining"] == 5

    run_httpie("POST", f"http://127.0.0.1:8001/timers/{timer_id}/resume")
    run_httpie("POST", "http://127.0.0.1:8001/tick", "seconds==3")
    data = run_httpie("GET", "http://127.0.0.1:8001/timers")
    assert data[str(timer_id)]["remaining"] == 2

    run_httpie("DELETE", f"http://127.0.0.1:8001/timers/{timer_id}")
    data = run_httpie("GET", "http://127.0.0.1:8001/timers")
    assert str(timer_id) not in data
