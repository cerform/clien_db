import time
import subprocess
from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_installer_router_and_job(monkeypatch, tmp_path):
    # Import module (should exist)
    from src.web import installer as installer_mod

    app = FastAPI()
    app.include_router(installer_mod.installer_router)
    client = TestClient(app)

    # Patch Popen so the background job writes a small log and exits quickly
    class DummyProc:
        def __init__(self, *a, **kw):
            stdout = kw.get('stdout')
            if stdout and hasattr(stdout, 'write'):
                stdout.write(b"[TEST] installer started\n")
                stdout.flush()
        def wait(self):
            return 0

    monkeypatch.setattr(subprocess, 'Popen', DummyProc)

    payload = {
        "project": "test-project",
        "region": "europe-west1",
        "service": "test-service",
        "telegram_token": "",
        "set_webhook": False,
    }

    r = client.post('/installer/start', json=payload)
    assert r.status_code == 200
    job = r.json()
    job_id = job['job_id']
    assert job_id

    # Wait briefly for background thread to complete
    for _ in range(20):
        sr = client.get(f'/installer/status/{job_id}').json()
        if sr.get('status') in ('succeeded', 'failed'):
            break
        time.sleep(0.1)

    sr = client.get(f'/installer/status/{job_id}').json()
    assert sr.get('status') in ('succeeded', 'failed')

    lr = client.get(f'/installer/logs/{job_id}').json()
    assert '[TEST] installer started' in lr.get('logs', '')
