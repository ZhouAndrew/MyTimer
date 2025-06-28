import subprocess
import requests
import time
import sys

SERVER_URL = "http://127.0.0.1:8000"


def wait_for_server(url: str, retries: int = 10) -> bool:
    for _ in range(retries):
        try:
            requests.get(url, timeout=1)
            return True
        except requests.RequestException:
            time.sleep(0.5)
    return False


def run_cmd(cmd):
    print("$", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip())


if __name__ == "__main__":
    print("Starting server...")
    server_proc = subprocess.Popen([
        "uvicorn",
        "api_server:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
        "--log-level",
        "warning",
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    try:
        if not wait_for_server(f"{SERVER_URL}/timers"):
            print("Failed to start server")
            sys.exit(1)
        print("Server started.\n")

        run_cmd([sys.executable, "client_controller.py", "create", "5"])
        run_cmd([sys.executable, "client_controller.py", "list"])
        run_cmd([sys.executable, "client_controller.py", "tick", "3"])
        run_cmd([sys.executable, "client_controller.py", "list"])
        run_cmd([sys.executable, "client_controller.py", "remove", "1"])
        run_cmd([sys.executable, "client_controller.py", "list"])
    finally:
        print("\nStopping server...")
        server_proc.terminate()
        server_proc.wait()
