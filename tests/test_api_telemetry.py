from fastapi.testclient import TestClient
from src.web.app import create_app


def test_post_telemetry_and_get_history():
    app = create_app()
    client = TestClient(app)

    payload = {
        "event_type": "ui_warning",
        "message": "test telemetry",
        "meta": {"x": 1}
    }

    r = client.post('/api/telemetry/events', json=payload)
    assert r.status_code == 200
    assert r.json().get('success') is True

    # Get history and check last event
    r2 = client.get('/api/telemetry/history')
    assert r2.status_code == 200
    history = r2.json().get('history')
    assert isinstance(history, list)
    assert any(h.get('message') == 'test telemetry' for h in history)
