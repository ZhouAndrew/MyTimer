from __future__ import annotations

"""Interactive CLI tool for editing MyTimer settings."""

import argparse
from pathlib import Path
from typing import Iterable

from client_settings import ClientSettings

SETTINGS_PATH = Path.home() / ".timercli" / "settings.json"


class CLISettings:
    """Terminal menu for updating :class:`ClientSettings`."""

    def __init__(self, path: Path = SETTINGS_PATH) -> None:
        self.path = path
        self.settings = ClientSettings.load(self.path)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.settings.save(self.path)

    def _prompt(self, prompt: str, iterator: Iterable[str] | None) -> str:
        if iterator is not None:
            try:
                return next(iterator).strip()
            except StopIteration:
                return ""
        return input(prompt).strip()

    def run_interactive(self, commands: Iterable[str] | None = None) -> None:
        it = iter(commands) if commands is not None else None
        while True:
            print(
                f"\nSettings file: {self.path}\n"
                f"1. Server URL: {self.settings.server_url}\n"
                f"2. Theme: {self.settings.theme}\n"
                f"3. Notifications Enabled: {self.settings.notifications_enabled}\n"
                f"4. Notify Sound: {self.settings.notify_sound}\n"
                "5. Save and exit\n"
                "q. Quit\n"
                "Choice: ",
                end="",
            )
            choice = self._prompt("", it)
            if choice == "1":
                value = self._prompt("Server URL: ", it)
                if value:
                    self.settings.server_url = value
            elif choice == "2":
                value = self._prompt("Theme: ", it)
                if value:
                    self.settings.theme = value
            elif choice == "3":
                value = self._prompt("Enable notifications (y/n): ", it).lower()
                if value in {"y", "yes"}:
                    self.settings.notifications_enabled = True
                elif value in {"n", "no"}:
                    self.settings.notifications_enabled = False
            elif choice == "4":
                value = self._prompt("Notify sound: ", it)
                if value:
                    self.settings.notify_sound = value
            elif choice == "5":
                self.save()
                print("Saved.")
                break
            elif choice.lower() in {"q", "quit", "exit"}:
                break
            else:
                print("Invalid choice")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Manage MyTimer CLI settings")
    parser.add_argument("--path", help="Settings file path")
    parser.add_argument("--server-url", help="API server URL")
    parser.add_argument("--theme", help="Color theme name")
    parser.add_argument("--enable-notify", action="store_true", help="Enable notifications")
    parser.add_argument("--disable-notify", action="store_true", help="Disable notifications")
    parser.add_argument("--notify-sound", help="Notification sound")
    parser.add_argument("--print", action="store_true", help="Print current settings")
    args = parser.parse_args(argv)

    config_path = Path(args.path) if args.path else SETTINGS_PATH
    cli = CLISettings(config_path)
    changed = False
    if args.server_url:
        cli.settings.server_url = args.server_url
        changed = True
    if args.theme:
        cli.settings.theme = args.theme
        changed = True
    if args.enable_notify:
        cli.settings.notifications_enabled = True
        changed = True
    if args.disable_notify:
        cli.settings.notifications_enabled = False
        changed = True
    if args.notify_sound:
        cli.settings.notify_sound = args.notify_sound
        changed = True

    if args.print and not changed:
        print(cli.settings)
        return

    if changed:
        cli.save()
    else:
        cli.run_interactive()


if __name__ == "__main__":
    main()

