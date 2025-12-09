import pytest
try:
    from playwright.sync_api import sync_playwright
except Exception:
    pytest.skip("Playwright not installed (skipping E2E tests)", allow_module_level=True)
import threading
import time
from src.web.app import create_app
import uvicorn


def run_app():
    app = create_app()
    uvicorn.run(app, host='127.0.0.1', port=8001, log_level='info')


@pytest.mark.slow
def test_ui_login_and_open_dashboard():
    # Start server in background thread
    thread = threading.Thread(target=run_app, daemon=True)
    thread.start()
    time.sleep(1)  # wait for the server

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('http://127.0.0.1:8001')
        assert 'Admin Panel' in page.title()

        # Optional: open login page
        page.goto('http://127.0.0.1:8001/login')
        assert 'login' in page.url
        browser.close()
    # shutdown
    # uvicorn doesn't easily shutdown in this simple setup; leaving thread as daemon
@pytest.mark.slow
def test_admin_create_and_delete_client_flow(mock_sheets_client):
    """E2E test that logs in and creates + deletes a client via the UI and checks audit logs."""
    import threading
    import time
    import uvicorn
    from src.web.app import create_app
    from playwright.sync_api import sync_playwright

    def run_app():
        app = create_app()
        # app will use patched GoogleSheetsClient (mock_sheets_client) thanks to fixture monkeypatch
        uvicorn.run(app, host='127.0.0.1', port=8002, log_level='info')

    thread = threading.Thread(target=run_app, daemon=True)
    thread.start()
    time.sleep(1.2)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Login
        page.goto('http://127.0.0.1:8002/login')
        page.fill('#username', 'admin')
        page.fill('#password', 'admin123')
        page.click('#submitBtn')
        page.wait_for_url('http://127.0.0.1:8002/')

        # Go to clients page
        page.goto('http://127.0.0.1:8002/clients')
        page.wait_for_selector('.btn')

        # Click add client
        page.click('button:has-text("Добавить клиента")')
        page.fill('#name', 'E2E Test Client')
        page.fill('#phone', '+10000000001')
        page.fill('#email', 'e2e@example.com')
        page.click('.btn-save')
        page.wait_for_selector('text=E2E Test Client')

        # Ensure the client is present
        assert page.locator('text=E2E Test Client').count() >= 1

        # Delete the client
        # Find the row and click delete button next to it
        # (we'll click first delete button in the row containing the name)
        row = page.locator('tr', has_text='E2E Test Client').first
        with page.expect_dialog() as dialog_info:
            row.locator('button.btn-delete').click()
        dialog = dialog_info.value
        dialog.accept()
        # Wait for success alert
        page.wait_for_selector('text=Клиент удален!')

        # Check audit logs via API: we expect add_client & delete_client entries
        # Page has `page.request` to do HTTP requests
        audit_resp = page.request.get('http://127.0.0.1:8002/api/audit/logs')
        assert audit_resp.ok
        logs = audit_resp.json()
        # Look for add_client & delete_client entries
        actions = [l.get('action') for l in logs]
        assert 'add_client' in actions or 'add_client' in str(logs)
        assert 'delete_client' in actions or 'delete_client' in str(logs)

        browser.close()
    # Thread remains as daemon
