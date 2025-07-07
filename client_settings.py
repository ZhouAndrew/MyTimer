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
    theme: str = "light"

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
            theme=data.get("theme", cls.theme),
        )

    def save(self, path: str | Path) -> None:
        """Write settings to ``path`` as JSON."""
        file_path = Path(path)
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(asdict(self), f)

    def update(self, **kwargs: Any) -> None:
        """Update attributes with provided keyword arguments."""
        for field in ("server_url", "notifications_enabled", "notify_sound", "theme"):
            if field in kwargs:
                setattr(self, field, kwargs[field])
