from rich.console import Console
from rich.panel import Panel


def main():
    console = Console()
    console.print(Panel('Hello, World!', width=30, title='Greeting'))


if __name__ == '__main__':
    main()
