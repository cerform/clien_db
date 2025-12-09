from fastapi.testclient import TestClient
from src.web.app import create_app

app = create_app()
client = TestClient(app)


def login_as_default_admin():
    res = client.post('/api/login', json={'username': 'admin', 'password': 'admin123'})
    assert res.status_code == 200
    data = res.json()
    assert data.get('success')
    token = data.get('token')
    assert token
    return token


def test_admin_endpoints_crud():
    token = login_as_default_admin()
    headers = {'Authorization': f'Bearer {token}'}

    # GET admins
    r = client.get('/api/admins', headers=headers)
    assert r.status_code == 200
    admins = r.json()
    assert isinstance(admins, list)

    # Create admin
    r2 = client.post('/api/admins', json={'username': 'pytest_admin', 'password': 'testpass', 'role': 'admin', 'telegram_id': '12345'}, headers=headers)
    assert r2.status_code == 200
    assert r2.json().get('success')

    # GET admins again - verify exists
    r3 = client.get('/api/admins', headers=headers)
    assert r3.status_code == 200
    admins = r3.json()
    created = next((a for a in admins if a['username'] == 'pytest_admin'), None)
    assert created is not None

    admin_id = created['id']

    # Update admin username
    r4 = client.put(f'/api/admins/{admin_id}', json={'username': 'pytest_admin_mod', 'role': 'admin'}, headers=headers)
    assert r4.status_code == 200
    assert r4.json().get('success')

    # Toggle status
    r5 = client.put(f'/api/admins/{admin_id}/toggle-status', headers=headers)
    assert r5.status_code == 200
    assert r5.json().get('success')

    # Change password
    r6 = client.post(f'/api/admins/{admin_id}/change-password', json={'new_password': 'newpass'}, headers=headers)
    assert r6.status_code == 200
    assert r6.json().get('success')

    # Delete admin
    r7 = client.delete(f'/api/admins/{admin_id}', headers=headers)
    assert r7.status_code == 200
    assert r7.json().get('success')

    # Final check
    r8 = client.get('/api/admins', headers=headers)
    assert r8.status_code == 200
    usernames = [a['username'] for a in r8.json()]
    assert 'pytest_admin_mod' not in usernames


def test_health_endpoint():
    r = client.get('/api/health')
    assert r.status_code == 200
    assert r.json().get('ok') is True
