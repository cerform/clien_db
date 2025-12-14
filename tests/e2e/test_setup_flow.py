import os
import pytest

try:
    from playwright.sync_api import sync_playwright
    _PLAYWRIGHT_AVAILABLE = True
except Exception:
    _PLAYWRIGHT_AVAILABLE = False


def test_setup_page_basic():
    # This is a placeholder Playwright test; in CI will require Playwright dependencies installed.
    # Skip if Playwright is not available (e.g., local unit test runs without Playwright installed)
    if not _PLAYWRIGHT_AVAILABLE:
        pytest.skip("Playwright not installed; skipping e2e test")

    base_url = os.getenv('SERVICE_URL', 'http://localhost:8000')
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"{base_url}/setup")
        assert page.locator('form').count() == 1
        assert page.locator('input[name="salon_name"]').count() == 1
        browser.close()
