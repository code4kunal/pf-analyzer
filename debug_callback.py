#!/usr/bin/env python3
"""
Simple test to debug callback manually
"""
from kiteconnect import KiteConnect
from config import settings

def test_token_generation(request_token):
    """Test generating access token from request token"""
    print(f"🔍 Testing token generation...")
    print(f"API Key: {settings.kite_api_key}")
    print(f"Request Token: {request_token}")

    try:
        kite = KiteConnect(api_key=settings.kite_api_key)

        print(f"📞 Calling generate_session...")
        data = kite.generate_session(request_token, api_secret=settings.kite_api_secret)

        print(f"✅ Success! Generated tokens:")
        print(f"   User ID: {data.get('user_id')}")
        print(f"   Access Token: {data.get('access_token')[:20]}...")
        print(f"   Refresh Token: {data.get('refresh_token')[:20]}...")

        # Test with access token
        kite.set_access_token(data['access_token'])
        profile = kite.profile()
        print(f"✅ Profile test successful: {profile.get('user_name')}")

        return data

    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    print("This script will help debug the token generation")
    print("After logging in to Kite, copy the request_token from the URL and run:")
    print("python debug_callback.py <request_token>")