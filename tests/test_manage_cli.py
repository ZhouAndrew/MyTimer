import subprocess
import sys


def run_manage(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "tools/manage.py", *args], capture_output=True, text=True
    )


def test_manage_cli_suggestion():
    result = run_manage("strt")
    assert result.returncode != 0
    assert "Did you mean 'start'" in result.stderr
