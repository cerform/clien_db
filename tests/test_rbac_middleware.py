from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.web.middleware import RBACMiddleware
from src.web.rbac_route import RBACRoute
from src.web.auth import permission_required


def create_test_app():
    app = FastAPI()
    app.add_middleware(RBACMiddleware)
    app.router.route_class = RBACRoute

    @app.get('/stats')
    @permission_required('view_stats')
    def stats():
        return {'ok': True}

    @app.post('/clients')
    @permission_required('add_client')
    def clients():
        return {'ok': True}

    return app


def test_rbac_middleware_admin_token_allows():
    app = create_test_app()
    client = TestClient(app)

    # Admin fallback token should be allowed
    headers = {'Authorization': 'Bearer admin_token_123'}
    r = client.get('/stats', headers=headers)
    assert r.status_code == 200
    r2 = client.post('/clients', headers=headers)
    assert r2.status_code == 200

def test_endpoint_metadata_set():
    app = create_test_app()
    route_endpoints = {r.path: r.endpoint for r in app.routes if hasattr(r, 'path')}
    assert '/stats' in route_endpoints
    assert '/clients' in route_endpoints
    assert hasattr(route_endpoints['/stats'], '__required_permission__')
    assert getattr(route_endpoints['/stats'], '__required_permission__') == 'view_stats'
    assert hasattr(route_endpoints['/clients'], '__required_permission__')
    assert getattr(route_endpoints['/clients'], '__required_permission__') == 'add_client'


def test_rbac_middleware_inka_can_add_client():
    app = create_test_app()
    client = TestClient(app)

    # INKA should be able to add clients
    headers = {'X-Requester': 'inka'}
    r = client.post('/clients', headers=headers)
    assert r.status_code == 200


def test_rbac_middleware_bot_cannot_add_client():
    app = create_test_app()
    client = TestClient(app)

    headers = {'X-Requester': 'bot'}
    r = client.post('/clients', headers=headers)
    assert r.status_code == 403
