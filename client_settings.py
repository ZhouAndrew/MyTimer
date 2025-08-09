from __future__ import annotations

"""Local configuration handling for MyTimer clients.

The settings were previously stored in JSON files.  To provide more robust
persistence and easier querying we now use a tiny SQLite database.  A single
table named ``settings`` stores one row with all configuration fields.  The
functions below transparently handle reading and writing this database while
preserving the same :class:`ClientSettings` API for callers.
"""

from dataclasses import dataclass, asdict
import json
import sqlite3
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
        """Load settings from ``path``.

        The file at ``path`` is treated as a SQLite database.  If the file or
        expected table is missing, default settings are returned.  Missing
        columns default to the dataclass values, allowing forward compatibility
        when new fields are introduced.
        """

        file_path = Path(path)
        if not file_path.exists():
            return cls()

        try:
            conn = sqlite3.connect(file_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='settings'"
            )
            if not cur.fetchone():
                return cls()
            cur.execute("SELECT * FROM settings WHERE id=1")
            row = cur.fetchone()
            if row is None:
                return cls()
            data = dict(row)
        except sqlite3.Error:
            return cls()
        finally:
            try:
                conn.close()
            except Exception:
                pass

        try:
            volume = float(data.get("volume", cls.volume))
        except (TypeError, ValueError):
            volume = cls.volume

        return cls(
            server_url=data.get("server_url", cls.server_url),
            notifications_enabled=bool(
                data.get("notifications_enabled", cls.notifications_enabled)
            ),
            notify_sound=data.get("notify_sound", cls.notify_sound),
            auth_token=data.get("auth_token"),
            device_name=data.get("device_name"),
            theme=data.get("theme", cls.theme),
            volume=volume,
            mute=bool(data.get("mute", cls.mute)),
        )

    def save(self, path: str | Path) -> None:
        """Persist settings to ``path`` as a SQLite database."""

        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(file_path)
        try:
            with conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS settings (
                        id INTEGER PRIMARY KEY,
                        server_url TEXT,
                        notifications_enabled INTEGER,
                        notify_sound TEXT,
                        auth_token TEXT,
                        device_name TEXT,
                        theme TEXT,
                        volume REAL,
                        mute INTEGER
                    )
                    """
                )
                conn.execute(
                    """
                    REPLACE INTO settings
                    (id, server_url, notifications_enabled, notify_sound,
                     auth_token, device_name, theme, volume, mute)
                    VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        self.server_url,
                        int(self.notifications_enabled),
                        self.notify_sound,
                        self.auth_token,
                        self.device_name,
                        self.theme,
                        float(self.volume),
                        int(self.mute),
                    ),
                )
        finally:
            conn.close()

    def update(self, **kwargs: Any) -> None:

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
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(asdict(self), f)

    @classmethod
    def import_json(cls, path: str | Path) -> "ClientSettings":
        """Load settings from JSON ``path`` and return a new instance."""

        file_path = Path(path)
        with file_path.open("r", encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)
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
