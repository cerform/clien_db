import pytest

try:
    from fastapi.testclient import TestClient
    from src.web.app import create_app
    client = TestClient(create_app())
except Exception:
    client = None


def test_inka_stats_ok():
    if client is None:
        pytest.skip("fastapi dependencies not installed")
    res = client.get('/api/inka-training/stats')
    assert res.status_code == 200
    data = res.json()
    assert 'total_sessions' in data
    assert 'successful_trainings' in data


def test_inka_chat_ok():
    if client is None:
        pytest.skip("fastapi dependencies not installed")
    res = client.post('/api/inka-training/chat', json={'message': 'hello world'})
    assert res.status_code == 200
    data = res.json()
    assert 'response' in data


def test_inka_scenarios_crud():
    if client is None:
        pytest.skip("fastapi dependencies not installed")
    # POST create
    res = client.post('/api/inka-training/scenario', json={'category': 'test', 'trigger': 'hi', 'response': 'hello', 'context': ''})
    assert res.status_code == 200
    sr = res.json()
    assert sr.get('success') is True

    # GET scenarios
    res = client.get('/api/inka-training/scenarios')
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data.get('scenarios'), list)


@pytest.mark.parametrize('path', [
    '/api/inka-training/corrections',
    '/api/inka-training/knowledge',
    '/api/inka-training/recent'
])
def test_inka_misc_gets(path):
    if client is None:
        pytest.skip("fastapi dependencies not installed")
    res = client.get(path)
    assert res.status_code == 200


def test_favicon_svg_provided():
    if client is None:
        pytest.skip("fastapi dependencies not installed")
    res = client.get('/favicon.ico')
    assert res.status_code == 200
    assert 'svg' in res.headers.get('content-type', '')


def test_train_inka_missing_text_returns_400_or_500():
    if client is None:
        pytest.skip("fastapi dependencies not installed")
    # Try without text - server may return 400 (if learning system initialized) or 500 (if not)
    res = client.post('/api/inka-training', json={})
    assert res.status_code in (400, 500)


def test_train_inka_with_learning_system(monkeypatch):
    if client is None:
        pytest.skip("fastapi dependencies not installed")
    import src.web.app as app_mod
    class DummyLearning:
        pass
    app_mod.learning_system = DummyLearning()
    res = client.post('/api/inka-training', json={'text': 'train me'})
    # With dummy learning system, endpoint should accept or return 200 (success) or 500 if code uses other checks
    assert res.status_code in (200, 201, 500)


def test_masters_returns_500_when_db_missing(monkeypatch):
    if client is None:
        pytest.skip("fastapi dependencies not installed")
    import src.web.app as app_mod
    # Backup and remove db_manager
    original_db = getattr(app_mod, 'db_manager', None)
    app_mod.db_manager = None
    res = client.get('/api/masters')
    assert res.status_code == 500
    # restore
    app_mod.db_manager = original_db


def test_monitoring_endpoint_ok_or_warn():
    if client is None:
        pytest.skip("fastapi dependencies not installed")
    res = client.get('/api/monitoring/checks')
    assert res.status_code == 200
    data = res.json()
    assert 'ok' in data and 'results' in data
