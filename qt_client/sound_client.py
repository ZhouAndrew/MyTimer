import requests


class SoundClient:
    """Client for the local sound server used by the Qt GUI."""

    def __init__(self, base_url: str = "http://127.0.0.1:8800") -> None:
        self.base_url = base_url.rstrip("/")

    def ring(self) -> None:
        """Trigger playback on the sound server. Errors are ignored."""
        try:
            requests.post(f"{self.base_url}/ring", timeout=3)
        except Exception:
            pass
