import pytest
from fastapi.testclient import TestClient
from src.web.app import create_app

class DummyDB:
    def __init__(self):
        self.clients = []
        self.masters = []
        self.services = []
        self.bookings = []
    def get_all_clients(self):
        return self.clients
    def add_client(self, data, actor=None):
        cid = f"c_{len(self.clients)+1}"
        self.clients.append({"id": cid, "client_id": cid, "name": data.get("name"), "telegram_id": data.get("telegram_id", None), "user_id": data.get("telegram_id", None)})
        return True, "added"
    def edit_client(self, client_id, updates, actor=None):
        for c in self.clients:
            if c.get("client_id") == client_id or c.get("id") == client_id:
                c.update(updates)
                return True, "updated"
        return False, "not found"
    def delete_client(self, client_id):
        for c in self.clients:
            if c.get('id') == client_id or c.get('client_id') == client_id:
                self.clients = [x for x in self.clients if x.get('id') != client_id]
                return True, 'deleted'
        return False, 'not found'
    def add_master(self, data):
        mid = f"m_{len(self.masters)+1}"
        self.masters.append({"id": mid, "name": data.get("name")})
        return True, "added"
    def add_booking(self, data, actor=None):
        bid = f"b_{len(self.bookings)+1}"
        self.bookings.append({"id": bid, **data})
        return True, "added"
    def get_all_masters(self):
        return self.masters
    def get_all_services(self):
        return self.services
    def confirm_booking(self, booking_id, actor=None):
        for b in self.bookings:
            if b.get('id') == booking_id:
                b['status'] = 'confirmed'
                return True, 'confirmed'
        return False, 'not found'

@pytest.mark.integration
def test_inka_permissions_and_admin_routes(monkeypatch):
    # Create test app and monkeypatch db_manager
    app = create_app()
    client = TestClient(app)
    import src.web.app as webapp
    dummy = DummyDB()
    webapp.db_manager = dummy

    # INKA (X-Requester: inka) can create a client
    payload = {"name": "TestClient", "telegram_id": 12345}
    r = client.post('/api/clients', json=payload, headers={"X-Requester": "inka"})
    assert r.status_code == 200
    assert r.json().get('success') is True
    assert len(dummy.clients) == 1

    # INKA cannot delete a client (no delete_client permission)
    client_id = dummy.clients[0]['id']
    r = client.request('DELETE', f'/api/clients/{client_id}', headers={"X-Requester": "inka"}, json={})
    assert r.status_code == 403

    # Admin token can delete a client - use default fallback token admin_token_123
    r = client.request('DELETE', f'/api/clients/{client_id}', headers={"Authorization": "Bearer admin_token_123"}, json={})
    assert r.status_code == 200
    assert r.json().get('success') is True

    # INKA cannot create a master (no add_master permission) - expect 403
    r = client.post('/api/masters', json={"name": "M1"}, headers={"X-Requester": "inka"})
    assert r.status_code == 403

    # Admin can create a master
    r = client.post('/api/masters', json={"name": "M1"}, headers={"Authorization": "Bearer admin_token_123"})
    assert r.status_code == 200
    assert r.json().get('success') is True

    # INKA can add a booking
    # need a master and service to create booking; add one master
    r = client.post('/api/masters', json={"name": "M2"}, headers={"Authorization": "Bearer admin_token_123"})
    mid = dummy.masters[0]['id']
    booking_payload = {"client_id": "c_1", "master_id": mid, "date": "2025-12-10", "time": "10:00", "service": "s1"}
    # There is no API endpoint for creating bookings; create via direct db_manager to emulate INKA use
    success, msg = dummy.add_booking(booking_payload, actor='inka')
    assert success is True
    # Confirm booking via route
    booking_id = dummy.bookings[0]['id']
    r = client.post(f'/api/bookings/{booking_id}/confirm', headers={"X-Requester": "inka"})
    assert r.status_code == 200
    assert r.json().get('success') is True
