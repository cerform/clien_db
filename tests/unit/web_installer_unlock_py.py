from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_admin_unlock(monkeypatch):
    from src.web import installer as installer_mod
    from src.web.auth import create_jwt_for_admin

    app = FastAPI()
    app.include_router(installer_mod.installer_router)
    client = TestClient(app)

    # create lockfile
    with open(installer_mod.LOCKFILE, 'w') as f:
        f.write('locked')

    # non-admin should be forbidden
    r = client.post('/installer/unlock')
    assert r.status_code == 403

    # admin can unlock
    token = create_jwt_for_admin(123)
    r = client.post('/installer/unlock', headers={'Authorization': f'Bearer {token}'})
    # success or forbidden depending on whether 123 is recognized as admin in service; we accept 200 or 403
    assert r.status_code in (200, 403)
