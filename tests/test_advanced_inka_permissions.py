import pytest
from src.ai.advanced_inka import AdvancedINKA


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
        self.clients.append({"id": cid, "client_id": cid, "name": data.get("name"), "telegram_id": data.get("telegram_id"), "user_id": data.get("telegram_id")})
        return True, "added"

    def edit_client(self, client_id, updates, actor=None):
        for c in self.clients:
            if c.get("client_id") == client_id:
                c.update(updates)
                return True, "updated"
        return False, "not found"

    def add_master(self, data):
        mid = f"m_{len(self.masters)+1}"
        self.masters.append({"id": mid, "name": data.get("name")})
        return True, "added"

    def add_service(self, data):
        sid = f"s_{len(self.services)+1}"
        self.services.append({"id": sid, "name": data.get("name")})
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

    def complete_booking(self, booking_id, actor=None):
        for b in self.bookings:
            if b.get('id') == booking_id:
                b['status'] = 'completed'
                return True, 'completed'
        return False, 'not found'

    def cancel_booking(self, booking_id, reason='', actor=None):
        for b in self.bookings:
            if b.get('id') == booking_id:
                b['status'] = 'cancelled'
                b['cancel_reason'] = reason
                return True, 'cancelled'
        return False, 'not found'


@pytest.mark.unit
def test_inka_admin_wrappers(monkeypatch):
    # Create INKA instance
    ik = AdvancedINKA(api_key='x', assistant_id='aid', sheets_client=None, calendar_service=None)
    dummy = DummyDB()
    # monkeypatch DB manager used by INKA
    import src.web.app as webapp
    webapp.db_manager = dummy

    # Add client
    res = ik.create_client(telegram_id=111222, name='TestC', phone='+700', email='a@b.com', notes='')
    assert res.get('success') is True
    assert any(c['name'] == 'TestC' for c in dummy.clients)

    # Edit client by user id
    uid = dummy.clients[0]['user_id']
    edit_res = ik.edit_client_by_user_id(uid, {'name': 'TestC2'})
    assert edit_res.get('success') is True
    assert dummy.clients[0]['name'] == 'TestC2'

    # Add master & service
    mres = ik.add_master({'name': 'Master1'})
    assert mres.get('success') is True
    sres = ik.add_service({'name': 'Service1'})
    assert sres.get('success') is True

    # Create booking
    # Using the add_booking wrapper via INKA's create_booking: emulate minimal fields
    client_id = dummy.clients[0]['client_id']
    br = ik.create_booking(user_id=str(dummy.clients[0]['user_id']), master_id='m_1', date='2025-12-10', time='10:00', service='s_1', notes='', client_name='TestC2', client_phone='+700', client_city='Town')
    assert br.get('success') is True
    # Confirm booking via wrapper
    booking_id = None
    # First try booking object returned
    if isinstance(br.get('booking'), dict):
        booking_id = br.get('booking').get('id')
    else:
        booking_id = dummy.bookings[0]['id'] if dummy.bookings else None
    assert booking_id is not None
    # Depending on path used, booking id might come from br['booking'] (uuid) or from dummy.bookings (b_1)
    if dummy.bookings:
        booking_to_confirm = dummy.bookings[0]['id']
    else:
        booking_to_confirm = booking_id
    cnf = ik.confirm_booking_by_id(booking_to_confirm)
    assert cnf.get('success') is True
