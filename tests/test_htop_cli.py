import subprocess
import sys


def test_htop_cli_once():
    result = subprocess.run([sys.executable, '-m', 'tools.htop_cli', '--once'], capture_output=True, text=True)
    assert result.returncode == 0
    assert 'Mini htop' in result.stdout
