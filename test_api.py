#!/usr/bin/env python3
"""
Test script for GrowFolio CMS API
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health check endpoint"""
    print("\n" + "="*60)
    print("TEST 1: Health Check")
    print("="*60)
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_login():
    """Test login endpoint"""
    print("\n" + "="*60)
    print("TEST 2: Login")
    print("="*60)
    payload = {
        "email": "admin@grow-folio.in",
        "password": "Admin@123"
    }
    response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Login successful!")
        print(f"User: {data['user']['full_name']} ({data['user']['role']})")
        print(f"Is Temp Password: {data['is_temp_password']}")
        return data['access_token']
    else:
        print(f"❌ Login failed: {response.json()}")
        return None

def test_me(token):
    """Test get current user endpoint"""
    print("\n" + "="*60)
    print("TEST 3: Get Current User (/api/auth/me)")
    print("="*60)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Current user retrieved!")
        print(f"User: {data['full_name']} ({data['email']})")
        print(f"Role: {data['role']}")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False

def test_list_users(token):
    """Test list users endpoint"""
    print("\n" + "="*60)
    print("TEST 4: List Users")
    print("="*60)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/users", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        users = response.json()
        print(f"✅ Found {len(users)} user(s)")
        for user in users:
            print(f"  - {user['full_name']} ({user['email']}) - {user['role']}")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False

def test_invite_user(token):
    """Test invite user endpoint"""
    print("\n" + "="*60)
    print("TEST 5: Invite New User")
    print("="*60)
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "email": "employee@grow-folio.in",
        "full_name": "Test Employee",
        "phone": "+91-9876543210",
        "role": "EMPLOYEE"
    }
    response = requests.post(f"{BASE_URL}/api/users/invite", json=payload, headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        user = response.json()
        print(f"✅ User invited successfully!")
        print(f"User: {user['full_name']} ({user['email']})")
        print(f"Role: {user['role']}")
        print(f"⚠️  Check console for email details (SMTP not configured)")
        return user['id']
    else:
        print(f"❌ Failed: {response.json()}")
        return None

def main():
    print("\n" + "="*60)
    print("GrowFolio CMS API Test Suite")
    print("="*60)

    # Test 1: Health check
    if not test_health():
        print("\n❌ Health check failed. Aborting tests.")
        return

    # Test 2: Login
    token = test_login()
    if not token:
        print("\n❌ Login failed. Aborting tests.")
        return

    # Test 3: Get current user
    test_me(token)

    # Test 4: List users
    test_list_users(token)

    # Test 5: Invite user
    test_invite_user(token)

    print("\n" + "="*60)
    print("✅ All tests completed!")
    print("="*60)
    print("\nNOTE: Email functionality will show in server logs")
    print("      (SMTP sends emails via help@grow-folio.in)")
    print()

if __name__ == "__main__":
    main()
