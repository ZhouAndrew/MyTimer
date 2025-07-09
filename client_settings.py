from __future__ import annotations

"""Local configuration handling for MyTimer clients."""

from dataclasses import dataclass, asdict
import json
from pathlib import Path
from typing import Any



@dataclass
class ClientSettings:
    """Persist and manage client-side configuration."""

    server_url: str = "http://127.0.0.1:8000"
    notifications_enabled: bool = True
    notify_sound: str = "default"

    auth_token: str | None = None
    device_name: str | None = None
    theme: str = "light"
    volume: float = 1.0
    mute: bool = False

    @classmethod
    def load(cls, path: str | Path) -> "ClientSettings":
        """Load settings from ``path``. Missing or invalid files return defaults."""
        file_path = Path(path)
        if not file_path.exists():
            return cls()
        try:
            with file_path.open("r", encoding="utf-8") as f:
                data: dict[str, Any] = json.load(f)
        except (json.JSONDecodeError, OSError):
            return cls()

        return cls(
            server_url=data.get("server_url", cls.server_url),
            notifications_enabled=data.get(
                "notifications_enabled", cls.notifications_enabled
            ),
            notify_sound=data.get("notify_sound", cls.notify_sound),
            auth_token=data.get("auth_token"),
            device_name=data.get("device_name"),
            theme=data.get("theme", cls.theme),
            volume=float(data.get("volume", cls.volume)),
            mute=bool(data.get("mute", cls.mute)),
        )

    def save(self, path: str | Path) -> None:
        """Write settings to ``path`` as JSON."""
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(asdict(self), f)

    def update(self, **kwargs: Any) -> None:
        """Update attributes with provided keyword arguments."""
        self.server_url = kwargs.get("server_url", self.server_url)
        self.notifications_enabled = kwargs.get(
            "notifications_enabled", self.notifications_enabled
        )
        self.notify_sound = kwargs.get("notify_sound", self.notify_sound)
        self.auth_token = kwargs.get("auth_token", self.auth_token)
        self.device_name = kwargs.get("device_name", self.device_name)
        self.theme = kwargs.get("theme", "blue")
        self.volume = kwargs.get("volume", 0.7)
        self.mute = kwargs.get("mute", True)
        """Update attributes with provided keyword arguments.

        Only a subset of fields are supported. Theme, volume and mute are
        intentionally ignored to keep user visual preferences unchanged when
        updating settings programmatically.
        """

        for field in (
            "server_url",
            "notifications_enabled",
            "notify_sound",
            "auth_token",
            "device_name",
        ):
            if field in kwargs:
                setattr(self, field, kwargs[field])

    def export_json(self, path: str | Path) -> None:
        """Export settings to ``path`` as JSON."""
        self.save(path)

    @classmethod
    def import_json(cls, path: str | Path) -> "ClientSettings":
        """Load settings from ``path`` using :meth:`load`."""
        return cls.load(path)
