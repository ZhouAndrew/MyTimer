import time
from typing import Any, Dict
import requests


class NetworkClient:
    """Simple REST client for the MyTimer server."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000") -> None:
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def list_timers(self) -> Dict[str, Any]:
        """Return timer state from the server with computed remaining time."""
        resp = self.session.get(f"{self.base_url}/timers", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        now = time.time()
        for info in data.values():
            start = info.get("start_at")
            if start is not None:
                remaining = max(0.0, info["duration"] - (now - start))
                info["remaining"] = remaining
                info["finished"] = remaining <= 0
            else:
                info.setdefault("remaining", info.get("duration", 0))
                info.setdefault("finished", False)
        return data

    def create_timer(self, duration: float) -> str:
        """Create a timer and return its identifier."""
        resp = self.session.post(
            f"{self.base_url}/timers", params={"duration": duration}, timeout=5
        )
        resp.raise_for_status()
        return str(resp.json()["timer_id"])

    def pause_timer(self, timer_id: str) -> None:
        self.session.post(f"{self.base_url}/timers/{timer_id}/pause", timeout=5).raise_for_status()

    def resume_timer(self, timer_id: str) -> None:
        self.session.post(f"{self.base_url}/timers/{timer_id}/resume", timeout=5).raise_for_status()
