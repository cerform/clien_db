import pytest
from fastapi.testclient import TestClient
from src.web.app import create_app

client = TestClient(create_app())

def test_telegram_webhook_without_token(monkeypatch):
    # Ensure the route responds gracefully if bot is not configured
    response = client.post('/telegram/webhook', json={})
    assert response.status_code == 200
    assert response.json().get('ok') in (True, False)
