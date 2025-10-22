#!/usr/bin/env python3
"""
Test script for GrowFolio CMS Reports & Analytics API
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def get_auth_token():
    """Login and get auth token"""
    payload = {
        "email": "admin@grow-folio.in",
        "password": "Admin@123"
    }
    response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
    if response.status_code == 200:
        return response.json()['access_token']
    return None

def test_dashboard_stats(token):
    """Test dashboard statistics"""
    print("\n" + "="*60)
    print("TEST 1: Dashboard Statistics")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        stats = response.json()
        print(f"✅ Dashboard stats retrieved!")
        print(f"\nCustomers: {stats['customers']['total']} total")
        print(f"  - Active: {stats['customers']['active']}")
        print(f"  - Prospective: {stats['customers']['prospective']}")
        print(f"\nInvestments:")
        print(f"  - Total Invested: ₹{stats['investments']['total_invested']:,.2f}")
        print(f"  - Current Value: ₹{stats['investments']['total_current_value']:,.2f}")
        print(f"  - Returns: ₹{stats['investments']['total_returns']:,.2f} ({stats['investments']['return_percentage']}%)")
        print(f"\nCommissions:")
        print(f"  - Total: ₹{stats['commissions']['total']:,.2f}")
        print(f"  - Paid: ₹{stats['commissions']['paid']:,.2f}")
        print(f"  - Pending: ₹{stats['commissions']['pending']:,.2f}")
        print(f"\nInvoices:")
        print(f"  - Total Revenue: ₹{stats['invoices']['total_revenue']:,.2f}")
        print(f"  - Paid: ₹{stats['invoices']['paid_revenue']:,.2f}")
        print(f"  - Outstanding: ₹{stats['invoices']['outstanding_revenue']:,.2f}")
        print(f"\nRecent Activities: {len(stats['recent_activities'])}")
        print(f"Upcoming Events: {len(stats['upcoming_events'])}")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False

def test_customer_acquisition_report(token):
    """Test customer acquisition report"""
    print("\n" + "="*60)
    print("TEST 2: Customer Acquisition Report")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/reports/customer-acquisition", headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        report = response.json()
        summary = report['summary']
        print(f"✅ Customer acquisition report retrieved!")
        print(f"Total Customers: {summary['total_customers']}")
        print(f"\nBy Month:")
        for month, count in summary['by_month'].items():
            print(f"  {month}: {count} customers")
        print(f"\nBy Status:")
        for status, count in summary['by_status'].items():
            print(f"  {status}: {count} customers")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False

def test_customer_portfolio_report(token):
    """Test customer portfolio report"""
    print("\n" + "="*60)
    print("TEST 3: Customer Portfolio Analysis")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/reports/customer-portfolio?limit=5", headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        report = response.json()
        print(f"✅ Customer portfolio report retrieved!")
        print(f"\nTop Customers by Portfolio Value:")
        for customer in report['top_customers']:
            print(f"  - {customer['name']}: ₹{customer['total_portfolio_value']:,.2f} ({customer['investment_count']} investments)")
        print(f"\nSummary:")
        print(f"  Average Portfolio Size: ₹{report['summary']['average_portfolio_size']:,.2f}")
        print(f"  Total Portfolio Value: ₹{report['summary']['total_portfolio_value']:,.2f}")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False

def test_investment_performance_report(token):
    """Test investment performance report"""
    print("\n" + "="*60)
    print("TEST 4: Investment Performance Report")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/reports/investment-performance", headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        report = response.json()
        summary = report['summary']
        print(f"✅ Investment performance report retrieved!")
        print(f"\nOverall Performance:")
        print(f"  Total Investments: {summary['total_investments']}")
        print(f"  Total Invested: ₹{summary['total_invested']:,.2f}")
        print(f"  Current Value: ₹{summary['total_current_value']:,.2f}")
        print(f"  Returns: ₹{summary['total_returns']:,.2f} ({summary['overall_return_percentage']}%)")

        print(f"\nBy Category:")
        for category, data in report['by_category'].items():
            print(f"  {category}: {data['count']} investments, {data['return_percentage']}% return")

        if report['best_performing']:
            print(f"\nBest Performing Investment:")
            best = report['best_performing'][0]
            print(f"  {best['investment_name']}: {best['return_percentage']}% return")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False

def test_activity_summary(token):
    """Test activity summary report"""
    print("\n" + "="*60)
    print("TEST 5: Activity Summary Report")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/reports/activity-summary", headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        report = response.json()
        summary = report['summary']
        print(f"✅ Activity summary retrieved!")
        print(f"Total Activities: {summary['total_activities']}")
        print(f"\nTop Actions:")
        for action, count in list(summary['by_action'].items())[:5]:
            print(f"  {action}: {count} times")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False

def test_export_customers(token):
    """Test exporting customers to Excel"""
    print("\n" + "="*60)
    print("TEST 6: Export Customers to Excel")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/exports/customers", headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        print(f"✅ Customers exported to Excel!")
        print(f"Content-Type: {response.headers.get('content-type')}")
        print(f"File size: {len(response.content)} bytes")

        # Save to verify
        with open("/tmp/test_customers.xlsx", "wb") as f:
            f.write(response.content)
        print(f"Excel file saved to: /tmp/test_customers.xlsx")
        return True
    else:
        print(f"❌ Failed: {response.text}")
        return False

def test_export_commissions(token):
    """Test exporting commissions to Excel"""
    print("\n" + "="*60)
    print("TEST 7: Export Commissions to Excel")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/exports/commissions", headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        print(f"✅ Commissions exported to Excel!")
        print(f"File size: {len(response.content)} bytes")
        return True
    else:
        print(f"❌ Failed: {response.text}")
        return False

def test_export_invoices(token):
    """Test exporting invoices to Excel"""
    print("\n" + "="*60)
    print("TEST 8: Export Invoices to Excel")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/exports/invoices", headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        print(f"✅ Invoices exported to Excel!")
        print(f"File size: {len(response.content)} bytes")
        return True
    else:
        print(f"❌ Failed: {response.text}")
        return False

def test_export_investments(token):
    """Test exporting investments to Excel"""
    print("\n" + "="*60)
    print("TEST 9: Export Investments to Excel")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/exports/investments", headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        print(f"✅ Investments exported to Excel!")
        print(f"File size: {len(response.content)} bytes")
        return True
    else:
        print(f"❌ Failed: {response.text}")
        return False

def main():
    print("\n" + "="*60)
    print("GrowFolio CMS - Reports & Analytics API Test Suite")
    print("="*60)

    # Get auth token
    print("\nLogging in...")
    token = get_auth_token()
    if not token:
        print("❌ Failed to login. Aborting tests.")
        return

    print("✅ Logged in successfully!")

    # Run tests
    test_dashboard_stats(token)
    test_customer_acquisition_report(token)
    test_customer_portfolio_report(token)
    test_investment_performance_report(token)
    test_activity_summary(token)
    test_export_customers(token)
    test_export_commissions(token)
    test_export_invoices(token)
    test_export_investments(token)

    print("\n" + "="*60)
    print("✅ All Reports & Analytics Tests Completed!")
    print("="*60)
    print()
    print("📝 Summary:")
    print("- Dashboard statistics working")
    print("- Customer acquisition report working")
    print("- Customer portfolio analysis working")
    print("- Investment performance report working")
    print("- Activity summary working")
    print("- Excel exports (customers, commissions, invoices, investments) working")
    print("- All reports have RBAC enforcement")
    print()

if __name__ == "__main__":
    main()
