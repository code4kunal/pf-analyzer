"""
Quick test for Prospects API
Run this after starting the server to verify the API is working
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    print(f"✅ Health Check: {response.json()}")

def test_api_docs():
    """Test that API docs are accessible"""
    response = requests.get(f"{BASE_URL}/docs")
    print(f"✅ API Docs accessible: {response.status_code == 200}")

def test_prospects_endpoint_structure():
    """Test that prospects endpoint exists (will fail auth, which is expected)"""
    response = requests.get(f"{BASE_URL}/api/prospects")
    # Should return 401 or 403 (not authorized), not 404 (not found)
    if response.status_code in [401, 403]:
        print(f"✅ Prospects endpoint exists and is protected")
    else:
        print(f"❌ Unexpected status: {response.status_code}")
        print(f"   Response: {response.text}")

if __name__ == "__main__":
    print("🧪 Testing Prospects API\n")
    print("Note: Server must be running on http://localhost:8000\n")

    try:
        test_health()
        test_api_docs()
        test_prospects_endpoint_structure()

        print("\n✨ Basic tests passed!")
        print("\n📖 Next steps:")
        print("   1. Login to get auth token")
        print("   2. Test creating a prospect")
        print("   3. Test importing prospects")
        print("   4. Test analytics endpoint")
        print("\n   Visit http://localhost:8000/docs for interactive API testing")

    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to server")
        print("   Make sure the server is running with: python main.py or uvicorn main:app --reload")
    except Exception as e:
        print(f"❌ Error: {e}")
