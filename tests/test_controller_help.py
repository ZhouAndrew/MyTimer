import subprocess
import sys


def test_help_command():
    proc = subprocess.Popen(
        [sys.executable, '-m', 'mytimer.client.controller', 'interactive'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    stdout, stderr = proc.communicate('help\nquit\n', timeout=5)
    assert proc.returncode == 0, stderr
    assert 'Available commands:' in stdout
