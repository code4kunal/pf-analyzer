"""
Pytest configuration for UI tests
"""
import pytest
from playwright.sync_api import sync_playwright

@pytest.fixture(scope="session")
def browser():
    """Fixture to provide browser instance"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()

@pytest.fixture(scope="function")
def page(browser):
    """Fixture to provide a new page for each test"""
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        ignore_https_errors=True
    )
    page = context.new_page()
    yield page
    context.close()

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment before all tests"""
    print("\n" + "="*80)
    print("Starting UI Test Suite for GrowFolio CMS")
    print("="*80 + "\n")
    yield
    print("\n" + "="*80)
    print("UI Test Suite Completed")
    print("="*80 + "\n")
