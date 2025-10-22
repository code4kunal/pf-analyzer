#!/usr/bin/env python3
"""
Test script for GrowFolio CMS Customer Management API
"""
import requests
import json
from datetime import date, datetime

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

def test_create_customer(token):
    """Test creating a customer"""
    print("\n" + "="*60)
    print("TEST 1: Create Customer")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "full_name": "Rajesh Kumar",
        "email": "rajesh.kumar@example.com",
        "phone": "+91-9876543210",
        "date_of_birth": "1980-05-15",
        "gender": "MALE",
        "pan_number": "ABCDE1234F",
        "address_line1": "123 MG Road",
        "city": "Mumbai",
        "state": "Maharashtra",
        "pincode": "400001",
        "annual_income": 1500000,
        "risk_profile": "MODERATE",
        "investment_goals": "Retirement planning and wealth creation",
        "status": "ACTIVE",
        "referral_source": "Friend referral"
    }

    response = requests.post(f"{BASE_URL}/api/customers", json=payload, headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        customer = response.json()
        print(f"✅ Customer created successfully!")
        print(f"Name: {customer['full_name']}")
        print(f"Email: {customer['email']}")
        print(f"Status: {customer['status']}")
        return customer['id']
    else:
        print(f"❌ Failed: {response.json()}")
        return None

def test_list_customers(token):
    """Test listing customers with search"""
    print("\n" + "="*60)
    print("TEST 2: List Customers")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/customers?page=1&page_size=10", headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {data['total']} customer(s)")
        print(f"Page: {data['page']}/{data['total_pages']}")
        for customer in data['items']:
            print(f"  - {customer['full_name']} ({customer['email']}) - {customer['status']}")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False

def test_search_customers(token):
    """Test customer search"""
    print("\n" + "="*60)
    print("TEST 3: Search Customers")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/customers?search=Rajesh", headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Search found {data['total']} result(s)")
        for customer in data['items']:
            print(f"  - {customer['full_name']} ({customer['email']})")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False

def test_add_family_member(token, customer_id):
    """Test adding family member"""
    print("\n" + "="*60)
    print("TEST 4: Add Family Member")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "full_name": "Priya Kumar",
        "relation": "Spouse",
        "date_of_birth": "1985-08-20",
        "phone": "+91-9876543211",
        "email": "priya.kumar@example.com"
    }

    response = requests.post(f"{BASE_URL}/api/customers/{customer_id}/family-members", json=payload, headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        member = response.json()
        print(f"✅ Family member added!")
        print(f"Name: {member['full_name']} ({member['relation']})")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False

def test_add_nominee(token, customer_id):
    """Test adding nominee"""
    print("\n" + "="*60)
    print("TEST 5: Add Nominee")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "full_name": "Priya Kumar",
        "relation": "Spouse",
        "date_of_birth": "1985-08-20",
        "percentage_share": 100
    }

    response = requests.post(f"{BASE_URL}/api/customers/{customer_id}/nominees", json=payload, headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        nominee = response.json()
        print(f"✅ Nominee added!")
        print(f"Name: {nominee['full_name']} - {nominee['percentage_share']}%")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False

def test_add_investment(token, customer_id):
    """Test adding investment"""
    print("\n" + "="*60)
    print("TEST 6: Add Investment")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "customer_id": customer_id,
        "investment_type": "MUTUAL_FUND",
        "investment_name": "HDFC Equity Fund",
        "description": "Large cap mutual fund",
        "invested_amount": 100000,
        "current_value": 115000,
        "units": 1000,
        "investment_date": "2024-01-15"
    }

    response = requests.post(f"{BASE_URL}/api/investments", json=payload, headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        investment = response.json()
        print(f"✅ Investment added!")
        print(f"Name: {investment['investment_name']}")
        print(f"Invested: ₹{investment['invested_amount']}")
        print(f"Current: ₹{investment['current_value']}")
        print(f"Returns: ₹{investment['returns_absolute']} ({investment['returns_percentage']:.2f}%)")
        return investment['id']
    else:
        print(f"❌ Failed: {response.json()}")
        return None

def test_add_communication(token, customer_id):
    """Test logging communication"""
    print("\n" + "="*60)
    print("TEST 7: Log Communication")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "customer_id": customer_id,
        "communication_type": "CALL",
        "subject": "Investment Portfolio Review",
        "content": "Discussed portfolio performance and suggested rebalancing",
        "duration_minutes": 15,
        "communication_date": datetime.now().isoformat()
    }

    response = requests.post(f"{BASE_URL}/api/communications", json=payload, headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        comm = response.json()
        print(f"✅ Communication logged!")
        print(f"Type: {comm['communication_type']}")
        print(f"Subject: {comm['subject']}")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False

def test_add_note(token, customer_id):
    """Test adding note"""
    print("\n" + "="*60)
    print("TEST 8: Add Note")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "customer_id": customer_id,
        "title": "Investment Strategy",
        "content": "Customer prefers conservative investments with steady returns",
        "is_private": False
    }

    response = requests.post(f"{BASE_URL}/api/notes", json=payload, headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        note = response.json()
        print(f"✅ Note added!")
        print(f"Title: {note['title']}")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False

def test_get_customer_detail(token, customer_id):
    """Test getting full customer details"""
    print("\n" + "="*60)
    print("TEST 9: Get Customer Details")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/customers/{customer_id}", headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        customer = response.json()
        print(f"✅ Customer details retrieved!")
        print(f"Name: {customer['full_name']}")
        print(f"Portfolio Value: ₹{customer['current_portfolio_value']}")
        print(f"Family Members: {len(customer['family_members'])}")
        print(f"Nominees: {len(customer['nominees'])}")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False

def test_get_customer_investments(token, customer_id):
    """Test getting customer investments"""
    print("\n" + "="*60)
    print("TEST 10: Get Customer Investments")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/customers/{customer_id}/investments", headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        investments = response.json()
        print(f"✅ Found {len(investments)} investment(s)")
        for inv in investments:
            print(f"  - {inv['investment_name']}: ₹{inv['current_value']} ({inv['returns_percentage']:.2f}%)")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False

def main():
    print("\n" + "="*60)
    print("GrowFolio CMS - Customer Management API Test Suite")
    print("="*60)

    # Get auth token
    print("\nLogging in...")
    token = get_auth_token()
    if not token:
        print("❌ Failed to login. Aborting tests.")
        return

    print("✅ Logged in successfully!")

    # Run tests
    customer_id = test_create_customer(token)
    if not customer_id:
        print("\n❌ Failed to create customer. Aborting remaining tests.")
        return

    test_list_customers(token)
    test_search_customers(token)
    test_add_family_member(token, customer_id)
    test_add_nominee(token, customer_id)
    investment_id = test_add_investment(token, customer_id)
    test_add_communication(token, customer_id)
    test_add_note(token, customer_id)
    test_get_customer_detail(token, customer_id)
    test_get_customer_investments(token, customer_id)

    print("\n" + "="*60)
    print("✅ All Customer Management Tests Completed!")
    print("="*60)
    print()

if __name__ == "__main__":
    main()
