import time
import subprocess
from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_installer_end_to_end_parses_url(monkeypatch, tmp_path):
    from src.web import installer as installer_mod

    app = FastAPI()
    app.include_router(installer_mod.installer_router)
    client = TestClient(app)

    # Dummy Popen that writes the expected deploy completed line into the logfile
    class DummyProc:
        def __init__(self, *a, **kw):
            stdout = kw.get('stdout')
            if stdout and hasattr(stdout, 'write'):
                stdout.write(b"Some logs...\n✅ Deploy completed. Visit https://deployed.example.com/setup\n")
                stdout.flush()
        def wait(self):
            return 0

    monkeypatch.setattr(subprocess, 'Popen', DummyProc)

    payload = {"project": "p", "region": "r", "service": "s", "telegram_token": "", "set_webhook": True, "dry_run": True}
    r = client.post('/installer/start', json=payload)
    assert r.status_code == 200
    job_id = r.json()['job_id']

    for _ in range(20):
        sr = client.get(f'/installer/status/{job_id}').json()
        if sr.get('status') in ('succeeded', 'failed'):
            break
        time.sleep(0.1)

    sr = client.get(f'/installer/status/{job_id}').json()
    assert sr.get('status') == 'succeeded'
    assert sr.get('result_url') == 'https://deployed.example.com/setup'
    # lockfile should exist
    assert __import__('os').path.exists(installer_mod.LOCKFILE)
