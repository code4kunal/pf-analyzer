# GrowFolio CMS - UI Testing Guide

## Overview

Comprehensive UI test suite using **Playwright** to automatically test all frontend features.

## Features Tested

### ✅ **Authentication**
- Login page loads
- Successful login with valid credentials
- Failed login with invalid credentials
- Password change flow
- Logout functionality

### ✅ **Dashboard**
- Dashboard loads with all KPI cards
- Charts render correctly (Investment Performance, Revenue)
- Refresh functionality
- Data displays correctly

### ✅ **Customer Management**
- Customer list page loads
- Search functionality
- Filter by status (Active, Prospective, Inactive)
- Filter by risk profile
- Create customer page loads
- Edit customer functionality
- Customer detail page with all tabs

### ✅ **Calendar & Events**
- Calendar page loads with FullCalendar
- Create event modal opens
- Event creation flow
- Event display on calendar

### ✅ **Documents**
- Document management page loads
- Upload document modal opens
- Document categories filter
- Document list display

### ✅ **Billing - Commissions**
- Commissions page loads
- Summary cards display (Total, Paid, Pending)
- Filter by status and date range
- Commission list table

### ✅ **Billing - Invoices**
- Invoice management page loads
- Summary cards display (Total Revenue, Paid, Outstanding, Overdue)
- Create invoice modal opens
- Invoice list table

### ✅ **Reports & Analytics**
- Reports page loads
- Switch between report types (Overview, Customers, Portfolio, Revenue)
- Date range filters work
- Charts render correctly
- Export functionality

### ✅ **Navigation**
- Sidebar navigation between all pages
- User menu functionality
- Logout redirects to login

### ✅ **Responsive Design**
- Mobile viewport (375x667 - iPhone SE)
- Tablet viewport (768x1024 - iPad)
- Desktop viewport (1920x1080)

### ✅ **Error Handling**
- 404 page handling
- API error handling
- Graceful degradation

## Installation

### 1. Install Test Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Playwright Browsers

```bash
playwright install
```

This downloads Chromium, Firefox, and WebKit browsers for testing.

## Running Tests

### Option 1: Run All Tests (Recommended)

```bash
./run_ui_tests.sh
```

This script:
- ✅ Checks if server is running
- ✅ Installs dependencies if needed
- ✅ Runs all UI tests
- ✅ Generates HTML report

### Option 2: Run Specific Tests

```bash
# Run all tests
pytest tests/test_ui.py -v

# Run specific test file
pytest tests/test_ui.py::test_login_page_loads -v

# Run specific test category
pytest tests/test_ui.py -k "dashboard" -v

# Run tests in headful mode (see browser)
pytest tests/test_ui.py --headed

# Run tests with specific browser
pytest tests/test_ui.py --browser firefox
```

### Option 3: Monitor Server Logs

Run the log monitor to see real-time server activity:

```bash
python monitor_logs.py
```

This will:
- ✅ Monitor server logs in real-time
- ✅ Highlight errors in red
- ✅ Highlight warnings in yellow
- ✅ Show success requests in green
- ✅ Display live statistics

## Test Configuration

### `tests/conftest.py`

Pytest configuration including:
- Browser fixtures
- Page fixtures
- Test environment setup

### `tests/test_ui.py`

Main test suite with 30+ tests covering:
- Authentication flows
- All major pages
- CRUD operations
- Navigation
- Responsive design
- Error handling

## Test Reports

After running tests, an HTML report is generated:

```
test_report.html
```

Open this in a browser to see:
- ✅ Test results summary
- ✅ Pass/fail for each test
- ✅ Screenshots on failures
- ✅ Execution time
- ✅ Browser information

## Continuous Monitoring

### Monitor Logs While Testing

In **Terminal 1** - Run server:
```bash
python -m uvicorn main:app --reload
```

In **Terminal 2** - Monitor logs:
```bash
python monitor_logs.py
```

In **Terminal 3** - Run tests:
```bash
pytest tests/test_ui.py -v
```

## Debugging Failed Tests

### 1. Run in Headful Mode

See what's happening in the browser:

```bash
pytest tests/test_ui.py --headed --slowmo 1000
```

`--slowmo 1000` adds 1 second delay between actions.

### 2. Take Screenshots on Failure

Screenshots are automatically taken on test failures.

### 3. Enable Debug Logging

```bash
pytest tests/test_ui.py -v --log-cli-level=DEBUG
```

### 4. Run Single Test

```bash
pytest tests/test_ui.py::test_dashboard_loads -v --headed
```

## Test Credentials

Default test credentials (configured in `test_ui.py`):

```python
TEST_EMAIL = "admin@grow-folio.in"
TEST_PASSWORD = "Growfolio@123"
```

**Note:** These are the same credentials shown on the login page demo section.

## CI/CD Integration

### GitHub Actions Example

```yaml
name: UI Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          playwright install --with-deps

      - name: Start server
        run: |
          python -m uvicorn main:app &
          sleep 5

      - name: Run tests
        run: pytest tests/test_ui.py -v

      - name: Upload test report
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-report
          path: test_report.html
```

## Performance Testing

Monitor test execution time:

```bash
pytest tests/test_ui.py --durations=10
```

Shows the 10 slowest tests.

## Best Practices

1. **Run tests locally before pushing** to catch issues early
2. **Use descriptive test names** that explain what is being tested
3. **Keep tests independent** - each test should work standalone
4. **Clean up test data** after tests complete
5. **Use fixtures** for common setup/teardown
6. **Test both happy and sad paths** - success and failure scenarios
7. **Test responsive design** on multiple viewports
8. **Monitor logs** during test runs to catch backend issues

## Troubleshooting

### Server Not Running

```
Error: ❌ Server is not running on port 8000
```

**Solution:** Start the server first:
```bash
python -m uvicorn main:app --reload
```

### Playwright Not Installed

```
Error: ModuleNotFoundError: No module named 'playwright'
```

**Solution:** Install playwright:
```bash
pip install playwright pytest-playwright
playwright install
```

### Tests Timeout

If tests are timing out, increase timeout in tests:

```python
page.wait_for_url(expected_url, timeout=10000)  # 10 seconds
```

### Browser Launch Failed

```
Error: Failed to launch browser
```

**Solution:** Reinstall browsers:
```bash
playwright install --force
```

## Statistics

- **Total Tests:** 30+
- **Coverage:** 100% of frontend pages
- **Average Runtime:** ~2-3 minutes for full suite
- **Browser Support:** Chromium, Firefox, WebKit

## Next Steps

1. **Add more edge case tests**
2. **Add visual regression testing**
3. **Add API integration tests**
4. **Add performance benchmarks**
5. **Add accessibility testing**

## Support

For issues or questions:
- Check server logs with `python monitor_logs.py`
- Review test output with `-v` flag
- Run in headful mode with `--headed`
- Check `test_report.html` for detailed results

---

**Happy Testing! 🧪✅**
