import subprocess
import sys


def test_hello_cli_output():
    result = subprocess.run([sys.executable, '-m', 'tools.hello_cli'], capture_output=True, text=True)
    assert result.returncode == 0
    assert 'Hello, World!' in result.stdout
