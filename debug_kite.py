#!/usr/bin/env python3
"""
Debug script to test Kite Connect API independently
"""
from kiteconnect import KiteConnect
from config import settings
import traceback

def test_kite_api():
    print("🔍 Debugging Kite Connect API...")
    print(f"API Key: {settings.kite_api_key}")
    print(f"API Secret: {'*' * len(settings.kite_api_secret) if settings.kite_api_secret else 'None'}")

    try:
        # Test 1: Initialize KiteConnect
        print("\n1️⃣ Testing KiteConnect initialization...")
        kite = KiteConnect(api_key=settings.kite_api_key)
        print("✅ KiteConnect initialized successfully")

        # Test 2: Generate login URL
        print("\n2️⃣ Testing login URL generation...")
        login_url = kite.login_url()
        print(f"✅ Login URL: {login_url}")

        # Test 3: Check if we can get instruments (public endpoint)
        print("\n3️⃣ Testing public endpoint (instruments)...")
        try:
            instruments = kite.instruments()
            print(f"✅ Got {len(instruments)} instruments from NSE")
        except Exception as e:
            print(f"⚠️ Instruments test failed (expected without login): {e}")

        return True, login_url

    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"🔍 Full traceback:")
        traceback.print_exc()
        return False, None

if __name__ == "__main__":
    success, login_url = test_kite_api()

    if success and login_url:
        print(f"\n🎉 Kite API is working! Next steps:")
        print(f"1. Visit: {login_url}")
        print(f"2. Login with your Zerodha credentials")
        print(f"3. Copy the request_token from the redirect URL")
        print(f"4. Use it to generate access token")
    else:
        print(f"\n❌ Kite API test failed. Please check your credentials.")