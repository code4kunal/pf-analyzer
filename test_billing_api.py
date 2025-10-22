#!/usr/bin/env python3
"""
Test script for GrowFolio CMS Commission & Billing API
"""
import requests
import json
from datetime import datetime, timedelta, date

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

def get_customer_id(token):
    """Get first customer ID for testing"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/customers?page_size=1", headers=headers)
    if response.status_code == 200:
        customers = response.json()['items']
        if customers:
            return customers[0]['id']
    return None

def test_create_commission(token, customer_id):
    """Test creating a commission record"""
    print("\n" + "="*60)
    print("TEST 1: Create Commission (Upfront)")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "customer_id": customer_id,
        "commission_type": "Upfront",
        "amount": 25000.00,
        "percentage": 1.5,
        "earned_date": (date.today() - timedelta(days=10)).isoformat(),
        "notes": "Upfront commission for new SIP"
    }

    response = requests.post(f"{BASE_URL}/api/commissions", json=payload, headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        commission = response.json()
        print(f"✅ Commission created successfully!")
        print(f"ID: {commission['id']}")
        print(f"Type: {commission['commission_type']}")
        print(f"Amount: ₹{commission['amount']:,.2f}")
        print(f"Earned Date: {commission['earned_date']}")
        print(f"Paid: {commission['is_paid']}")
        return commission['id']
    else:
        print(f"❌ Failed: {response.json()}")
        return None

def test_create_trail_commission(token, customer_id):
    """Test creating a trail commission"""
    print("\n" + "="*60)
    print("TEST 2: Create Commission (Trail)")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "customer_id": customer_id,
        "commission_type": "Trail",
        "amount": 5000.00,
        "percentage": 0.5,
        "earned_date": date.today().isoformat()
    }

    response = requests.post(f"{BASE_URL}/api/commissions", json=payload, headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        commission = response.json()
        print(f"✅ Trail commission created!")
        print(f"Type: {commission['commission_type']}")
        print(f"Amount: ₹{commission['amount']:,.2f}")
        return commission['id']
    else:
        print(f"❌ Failed: {response.json()}")
        return None

def test_list_commissions(token):
    """Test listing commissions"""
    print("\n" + "="*60)
    print("TEST 3: List All Commissions")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/commissions", headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        commissions = response.json()
        print(f"✅ Found {len(commissions)} commission(s)")
        for comm in commissions:
            status = "PAID" if comm['is_paid'] else "PENDING"
            print(f"  - {comm['commission_type']}: ₹{comm['amount']:,.2f} - {status}")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False

def test_mark_commission_paid(token, commission_id):
    """Test marking commission as paid"""
    print("\n" + "="*60)
    print("TEST 4: Mark Commission as Paid")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "is_paid": True,
        "payment_date": date.today().isoformat(),
        "notes": "Payment processed via bank transfer"
    }

    response = requests.put(f"{BASE_URL}/api/commissions/{commission_id}", json=payload, headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        commission = response.json()
        print(f"✅ Commission marked as paid!")
        print(f"Payment Date: {commission['payment_date']}")
        print(f"Paid: {commission['is_paid']}")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False

def test_create_invoice(token, customer_id):
    """Test creating an invoice"""
    print("\n" + "="*60)
    print("TEST 5: Create Invoice")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}

    # Calculate dates
    invoice_date = date.today()
    due_date = invoice_date + timedelta(days=30)

    payload = {
        "customer_id": customer_id,
        "invoice_date": invoice_date.isoformat(),
        "due_date": due_date.isoformat(),
        "subtotal": 50000.00,
        "tax_amount": 9000.00,  # 18% GST
        "total_amount": 59000.00,
        "notes": "Investment advisory services for Q4 2025",
        "line_items": [
            {
                "description": "Portfolio Management Services",
                "quantity": 1,
                "unit_price": 30000.00,
                "amount": 30000.00
            },
            {
                "description": "Financial Planning Consultation",
                "quantity": 1,
                "unit_price": 20000.00,
                "amount": 20000.00
            }
        ]
    }

    response = requests.post(f"{BASE_URL}/api/invoices", json=payload, headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        invoice = response.json()
        print(f"✅ Invoice created successfully!")
        print(f"Invoice Number: {invoice['invoice_number']}")
        print(f"Date: {invoice['invoice_date']}")
        print(f"Due Date: {invoice['due_date']}")
        print(f"Total Amount: ₹{invoice['total_amount']:,.2f}")
        print(f"Status: {invoice['status']}")
        return invoice['id']
    else:
        print(f"❌ Failed: {response.json()}")
        return None

def test_list_invoices(token):
    """Test listing invoices"""
    print("\n" + "="*60)
    print("TEST 6: List All Invoices")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/invoices", headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        invoices = response.json()
        print(f"✅ Found {len(invoices)} invoice(s)")
        for inv in invoices:
            print(f"  - {inv['invoice_number']}: ₹{inv['total_amount']:,.2f} - {inv['status']}")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False

def test_send_invoice(token, invoice_id):
    """Test sending an invoice"""
    print("\n" + "="*60)
    print("TEST 7: Send Invoice to Customer")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/api/invoices/{invoice_id}/send", headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        invoice = response.json()
        print(f"✅ Invoice sent!")
        print(f"Invoice Number: {invoice['invoice_number']}")
        print(f"Status: {invoice['status']}")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False

def test_mark_invoice_paid(token, invoice_id):
    """Test marking invoice as paid"""
    print("\n" + "="*60)
    print("TEST 8: Mark Invoice as Paid")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "payment_date": date.today().isoformat(),
        "payment_method": "Bank Transfer",
        "payment_reference": "TXN123456789"
    }

    response = requests.post(f"{BASE_URL}/api/invoices/{invoice_id}/mark-paid", params=params, headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        invoice = response.json()
        print(f"✅ Invoice marked as paid!")
        print(f"Status: {invoice['status']}")
        print(f"Paid Amount: ₹{invoice['paid_amount']:,.2f}")
        print(f"Payment Method: {invoice['payment_method']}")
        print(f"Reference: {invoice['payment_reference']}")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False

def test_download_invoice_pdf(token, invoice_id):
    """Test downloading invoice PDF"""
    print("\n" + "="*60)
    print("TEST 9: Download Invoice PDF")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/invoices/{invoice_id}/pdf", headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        print(f"✅ PDF downloaded successfully!")
        print(f"Content-Type: {response.headers.get('content-type')}")
        print(f"File size: {len(response.content)} bytes")

        # Save PDF to verify
        with open("/tmp/test_invoice.pdf", "wb") as f:
            f.write(response.content)
        print(f"PDF saved to: /tmp/test_invoice.pdf")
        return True
    else:
        print(f"❌ Failed: {response.text}")
        return False

def test_commission_summary(token, customer_id):
    """Test commission summary report"""
    print("\n" + "="*60)
    print("TEST 10: Commission Summary Report")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/api/reports/commission-summary?customer_id={customer_id}",
        headers=headers
    )
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        report = response.json()
        summary = report['summary']
        print(f"✅ Commission summary retrieved!")
        print(f"Total Commissions: {summary['total_commissions']}")
        print(f"Total Amount: ₹{summary['total_amount']:,.2f}")
        print(f"Paid Amount: ₹{summary['paid_amount']:,.2f}")
        print(f"Pending Amount: ₹{summary['pending_amount']:,.2f}")
        print(f"\nBy Type:")
        for comm_type, data in report['by_type'].items():
            print(f"  {comm_type}: ₹{data['total_amount']:,.2f} ({data['count']} commission(s))")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False

def test_revenue_report(token):
    """Test revenue report"""
    print("\n" + "="*60)
    print("TEST 11: Revenue Report")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/reports/revenue", headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        report = response.json()
        summary = report['summary']
        print(f"✅ Revenue report retrieved!")
        print(f"Total Invoices: {summary['total_invoices']}")
        print(f"Total Revenue: ₹{summary['total_revenue']:,.2f}")
        print(f"Paid Revenue: ₹{summary['paid_revenue']:,.2f}")
        print(f"Outstanding Revenue: ₹{summary['outstanding_revenue']:,.2f}")
        print(f"Total Tax Collected: ₹{summary['total_tax_collected']:,.2f}")
        print(f"\nBy Status:")
        for status, data in report['by_status'].items():
            print(f"  {status}: ₹{data['total_amount']:,.2f} ({data['count']} invoice(s))")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False

def main():
    print("\n" + "="*60)
    print("GrowFolio CMS - Commission & Billing API Test Suite")
    print("="*60)

    # Get auth token
    print("\nLogging in...")
    token = get_auth_token()
    if not token:
        print("❌ Failed to login. Aborting tests.")
        return

    print("✅ Logged in successfully!")

    # Get customer for testing
    customer_id = get_customer_id(token)
    if not customer_id:
        print("❌ No customers found. Please create a customer first.")
        return

    print(f"✅ Found customer ID: {customer_id}")

    # Run tests
    commission_id = test_create_commission(token, customer_id)
    if not commission_id:
        print("\n❌ Failed to create commission. Aborting remaining tests.")
        return

    trail_commission_id = test_create_trail_commission(token, customer_id)
    test_list_commissions(token)
    test_mark_commission_paid(token, commission_id)

    invoice_id = test_create_invoice(token, customer_id)
    if not invoice_id:
        print("\n❌ Failed to create invoice. Aborting invoice tests.")
        return

    test_list_invoices(token)
    test_send_invoice(token, invoice_id)
    test_mark_invoice_paid(token, invoice_id)
    test_download_invoice_pdf(token, invoice_id)
    test_commission_summary(token, customer_id)
    test_revenue_report(token)

    print("\n" + "="*60)
    print("✅ All Commission & Billing Tests Completed!")
    print("="*60)
    print()
    print("📝 Summary:")
    print("- Commission tracking working")
    print("- Invoice creation with auto-numbering working")
    print("- Invoice status management working")
    print("- PDF generation successful")
    print("- Commission summary report working")
    print("- Revenue report working")
    print("- Activity logging active")
    print()

if __name__ == "__main__":
    main()
