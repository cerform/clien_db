import os
import time
from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_allowed_flag_and_lockfile(monkeypatch, tmp_path):
    from src.web import installer as installer_mod
    app = FastAPI()
    app.include_router(installer_mod.installer_router)
    client = TestClient(app)

    # Ensure no lockfile exists
    lock = installer_mod.LOCKFILE
    if os.path.exists(lock):
        os.unlink(lock)

    r = client.get('/installer/allowed')
    assert r.status_code == 200
    assert r.json().get('allowed') is True

    # Create a fake lockfile
    with open(lock, 'w') as f:
        f.write('locked')

    r = client.get('/installer/allowed')
    assert r.json().get('allowed') is False

    # Admin bypass: create token and call allowed with header
    from src.web.auth import create_jwt_for_admin
    token = create_jwt_for_admin(123)
    r = client.get('/installer/allowed', headers={'Authorization': f'Bearer {token}'})
    assert 'allowed' in r.json()


def test_start_forbidden_when_locked(monkeypatch, tmp_path):
    from src.web import installer as installer_mod
    app = FastAPI()
    app.include_router(installer_mod.installer_router)
    client = TestClient(app)

    lock = installer_mod.LOCKFILE
    # create lockfile
    with open(lock, 'w') as f:
        f.write('locked')

    payload = {"project": "p", "region": "r", "service": "s", "telegram_token": "", "set_webhook": False}
    r = client.post('/installer/start', json=payload)
    assert r.status_code == 403
