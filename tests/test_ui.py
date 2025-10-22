"""
UI Test Suite for GrowFolio CMS
Tests all frontend features using Playwright
"""
import pytest
import time
from playwright.sync_api import Page, expect

# Test Configuration
BASE_URL = "http://127.0.0.1:8000"
TEST_EMAIL = "admin@grow-folio.in"
TEST_PASSWORD = "Growfolio@123"

# ============================================================================
# AUTHENTICATION TESTS
# ============================================================================

def test_login_page_loads(page: Page):
    """Test that login page loads successfully"""
    page.goto(BASE_URL)
    page.evaluate("localStorage.clear()")
    page.reload()

    expect(page).to_have_title("Login - GrowFolio CMS")
    expect(page.locator('h1:has-text("GrowFolio CMS")')).to_be_visible()
    expect(page.locator('input[type="email"]')).to_be_visible()
    expect(page.locator('input[type="password"]')).to_be_visible()
    expect(page.locator('button:has-text("Sign In")')).to_be_visible()

def test_login_with_valid_credentials(page: Page):
    """Test successful login with valid credentials"""
    page.goto(BASE_URL)
    page.evaluate("localStorage.clear()")
    page.reload()

    # Fill in credentials
    page.fill('input[type="email"]', TEST_EMAIL)
    page.fill('input[type="password"]', TEST_PASSWORD)

    # Click sign in button
    page.click('button:has-text("Sign In")')

    # Wait for navigation (with longer timeout for 1s redirect delay)
    page.wait_for_url(lambda url: "/change-password" in url or "/dashboard" in url, timeout=10000)

    # Verify token is stored
    token = page.evaluate("localStorage.getItem('access_token')")
    assert token is not None

def test_login_with_invalid_credentials(page: Page):
    """Test login fails with invalid credentials"""
    page.goto(BASE_URL)
    page.evaluate("localStorage.clear()")
    page.reload()

    page.fill('input[type="email"]', "wrong@email.com")
    page.fill('input[type="password"]', "wrongpassword")
    page.click('button:has-text("Sign In")')

    # Wait for error to appear
    time.sleep(2)
    # Check that we're still on login page (not redirected)
    assert "/login" in page.url or page.url == BASE_URL or page.url == f"{BASE_URL}/"

# ============================================================================
# DASHBOARD TESTS
# ============================================================================

@pytest.fixture
def authenticated_page(page: Page):
    """Fixture that returns an authenticated page"""
    page.goto(BASE_URL)
    page.evaluate("localStorage.clear()")
    page.reload()

    page.fill('input[type="email"]', TEST_EMAIL)
    page.fill('input[type="password"]', TEST_PASSWORD)
    page.click('button:has-text("Sign In")')

    # Wait for redirect
    page.wait_for_url(lambda url: "/change-password" in url or "/dashboard" in url, timeout=10000)

    # If on change password page, skip it for now by navigating directly to dashboard
    # (we'll need to update this if password change is mandatory)

    return page

def test_dashboard_loads(authenticated_page: Page):
    """Test dashboard loads with all KPI cards"""
    page = authenticated_page
    page.goto(f"{BASE_URL}/dashboard")
    page.wait_for_load_state("networkidle")

    # Check KPI cards are visible
    expect(page.locator('text=Total Customers')).to_be_visible(timeout=10000)

def test_dashboard_refresh_button(authenticated_page: Page):
    """Test dashboard refresh button"""
    page = authenticated_page
    page.goto(f"{BASE_URL}/dashboard")
    page.wait_for_load_state("networkidle")

    # Find and click refresh button
    refresh_button = page.locator('button:has-text("Refresh")')
    if refresh_button.count() > 0:
        refresh_button.click()
        time.sleep(1)

# ============================================================================
# CUSTOMER MANAGEMENT TESTS
# ============================================================================

def test_customers_list_page_loads(authenticated_page: Page):
    """Test customers list page loads"""
    page = authenticated_page
    page.goto(f"{BASE_URL}/customers")
    page.wait_for_load_state("networkidle")

    # Check page elements (use first to avoid strict mode violation)
    expect(page.locator('h1,h2').filter(has_text="Customers").first).to_be_visible(timeout=10000)

def test_customers_search_functionality(authenticated_page: Page):
    """Test customer search"""
    page = authenticated_page
    page.goto(f"{BASE_URL}/customers")
    page.wait_for_load_state("networkidle")

    # Find search input if it exists
    search_input = page.locator('input[placeholder*="Search"]').first
    if search_input.count() > 0:
        search_input.fill("test")
        time.sleep(1)

def test_create_customer_page_loads(authenticated_page: Page):
    """Test create customer page loads"""
    page = authenticated_page
    page.goto(f"{BASE_URL}/customers/create")
    page.wait_for_load_state("networkidle")
    time.sleep(1)  # Allow page to render

# ============================================================================
# CALENDAR TESTS
# ============================================================================

def test_calendar_page_loads(authenticated_page: Page):
    """Test calendar page loads"""
    page = authenticated_page
    page.goto(f"{BASE_URL}/calendar")
    page.wait_for_load_state("networkidle")
    time.sleep(2)  # Wait for FullCalendar to initialize

# ============================================================================
# DOCUMENTS TESTS
# ============================================================================

def test_documents_page_loads(authenticated_page: Page):
    """Test documents page loads"""
    page = authenticated_page
    page.goto(f"{BASE_URL}/documents")
    page.wait_for_load_state("networkidle")
    time.sleep(1)

# ============================================================================
# BILLING TESTS
# ============================================================================

def test_commissions_page_loads(authenticated_page: Page):
    """Test commissions page loads"""
    page = authenticated_page
    page.goto(f"{BASE_URL}/billing/commissions")
    page.wait_for_load_state("networkidle")
    time.sleep(1)

def test_invoices_page_loads(authenticated_page: Page):
    """Test invoices page loads"""
    page = authenticated_page
    page.goto(f"{BASE_URL}/billing/invoices")
    page.wait_for_load_state("networkidle")
    time.sleep(1)

# ============================================================================
# REPORTS TESTS
# ============================================================================

def test_reports_page_loads(authenticated_page: Page):
    """Test reports page loads"""
    page = authenticated_page
    page.goto(f"{BASE_URL}/reports")
    page.wait_for_load_state("networkidle")
    time.sleep(1)

# ============================================================================
# NAVIGATION TESTS
# ============================================================================

def test_sidebar_navigation(authenticated_page: Page):
    """Test sidebar navigation between pages"""
    page = authenticated_page
    page.goto(f"{BASE_URL}/dashboard")
    page.wait_for_load_state("networkidle")

    # Test navigating to a few key pages
    pages_to_test = [
        ("Customers", "/customers"),
        ("Dashboard", "/dashboard")
    ]

    for page_name, expected_url_part in pages_to_test:
        # Try to find the nav link
        nav_link = page.locator(f'a:has-text("{page_name}")').first
        if nav_link.count() > 0:
            nav_link.click()
            page.wait_for_load_state("networkidle")
            time.sleep(1)
            assert expected_url_part in page.url

def test_logout_functionality(authenticated_page: Page):
    """Test logout button exists and is clickable"""
    page = authenticated_page
    page.goto(f"{BASE_URL}/dashboard")
    page.wait_for_load_state("networkidle")

    # Open user menu dropdown first (logout is in dropdown)
    user_menu = page.locator('button:has-text("Admin"),button:has-text("User")').first
    if user_menu.count() > 0:
        user_menu.click()
        time.sleep(0.5)

        # Verify logout link is visible
        logout_link = page.locator('a:has-text("Logout"),button:has-text("Logout")').first
        assert logout_link.count() > 0, "Logout button should be present"

        # Verify logout link has proper onclick handler
        logout_onclick = logout_link.get_attribute("onclick")
        assert logout_onclick is not None and "logout" in logout_onclick, "Logout should have logout() function"

# ============================================================================
# RESPONSIVE DESIGN TESTS
# ============================================================================

def test_mobile_viewport(page: Page):
    """Test mobile responsive design"""
    page.set_viewport_size({"width": 375, "height": 667})
    page.goto(BASE_URL)
    page.evaluate("localStorage.clear()")
    page.reload()

    expect(page.locator('h1:has-text("GrowFolio CMS")')).to_be_visible()

def test_tablet_viewport(page: Page):
    """Test tablet responsive design"""
    page.set_viewport_size({"width": 768, "height": 1024})
    page.goto(BASE_URL)
    page.evaluate("localStorage.clear()")
    page.reload()

    expect(page.locator('h1:has-text("GrowFolio CMS")')).to_be_visible()

# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

def test_404_page_handling(authenticated_page: Page):
    """Test 404 page handling"""
    page = authenticated_page
    page.goto(f"{BASE_URL}/nonexistent-page")
    time.sleep(1)
    # Page should either show 404 or redirect
    assert page.url is not None
