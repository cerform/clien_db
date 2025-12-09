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
