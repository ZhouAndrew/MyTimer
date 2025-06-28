import argparse
import time

import psutil
from rich.console import Console
from rich.live import Live
from rich.table import Table


def create_table() -> Table:
    """Return a table with CPU and memory usage."""
    cpu_percents = psutil.cpu_percent(percpu=True)
    memory = psutil.virtual_memory().percent

    table = Table(title="Mini htop")
    table.add_column("CPU Core", justify="right")
    table.add_column("Usage (%)", justify="right")

    for idx, usage in enumerate(cpu_percents):
        table.add_row(str(idx), f"{usage}")

    table.add_row("Memory", f"{memory}")
    return table


def main(once: bool = False) -> None:
    console = Console()
    if once:
        console.print(create_table())
    else:
        with Live(console=console, refresh_per_second=1) as live:
            while True:
                live.update(create_table())
                time.sleep(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mini htop-style monitor")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    args = parser.parse_args()
    main(args.once)
