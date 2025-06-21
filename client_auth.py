"""Simple token-based client authentication module."""

from __future__ import annotations

import uuid
from typing import Dict, Optional

from fastapi import Header, HTTPException, status


class ClientAuth:
    """Manage device tokens for authenticating API clients."""

    def __init__(self) -> None:
        self._tokens: Dict[str, str] = {}

    def register_device(self, token: Optional[str] = None) -> tuple[str, str]:
        """Register a new device token.

        Parameters
        ----------
        token:
            Optional pre-defined token. If not provided, a random token is
            generated.

        Returns
        -------
        tuple[str, str]
            The token and associated device ID.
        """
        if token is None:
            token = uuid.uuid4().hex
        device_id = uuid.uuid4().hex
        self._tokens[token] = device_id
        return token, device_id

    def validate(self, token: str) -> Optional[str]:
        """Return the device_id for ``token`` if valid."""
        return self._tokens.get(token)

    def remove_token(self, token: str) -> None:
        """Remove ``token`` from registry if it exists."""
        self._tokens.pop(token, None)

    async def dependency(self, token: Optional[str] = Header(None, alias="X-Auth-Token")) -> str:
        """FastAPI dependency to ensure a valid auth token is present."""
        if token is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Missing token")
        device_id = self.validate(token)
        if not device_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Invalid token")
        return device_id
