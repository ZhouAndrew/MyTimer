import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

from client_auth import ClientAuth


def create_app_and_auth():
    auth = ClientAuth()
    token, device_id = auth.register_device()

    app = FastAPI()

    @app.get("/protected")
    async def protected(did: str = Depends(auth.dependency)):
        return {"device_id": did}

    return app, auth, token, device_id


def test_protected_requires_token():
    app, _, _, _ = create_app_and_auth()
    client = TestClient(app)
    resp = client.get("/protected")
    assert resp.status_code == 401


def test_protected_with_valid_token():
    app, _, token, device_id = create_app_and_auth()
    client = TestClient(app)
    resp = client.get("/protected", headers={"X-Auth-Token": token})
    assert resp.status_code == 200
    assert resp.json()["device_id"] == device_id


def test_protected_with_invalid_token():
    app, _, token, _ = create_app_and_auth()
    client = TestClient(app)
    resp = client.get("/protected", headers={"X-Auth-Token": "bad"})
    assert resp.status_code == 401
