#!/usr/bin/env python3
"""
Test token generation with the request tokens we captured
"""
from kiteconnect import KiteConnect
from config import settings
from database import SessionLocal
from models import User

def test_with_captured_token():
    # Use one of the captured request tokens from the logs
    request_token = "eUe9AeJjLei5eg3MVXQ7aXLDqsGdNCsE"  # Latest from logs

    print(f"🔍 Testing with captured request token: {request_token}")

    try:
        kite = KiteConnect(api_key=settings.kite_api_key)

        print(f"📞 Generating session...")
        data = kite.generate_session(request_token, api_secret=settings.kite_api_secret)

        print(f"✅ Success! Generated:")
        print(f"   User ID: {data.get('user_id')}")
        print(f"   Access Token: {data.get('access_token')[:20]}...")

        # Test saving to database
        db = SessionLocal()
        user = db.query(User).filter(User.id == 1).first()
        if user:
            user.kite_user_id = data.get("user_id")
            user.kite_access_token = data.get("access_token")
            user.kite_refresh_token = data.get("refresh_token")
            db.commit()
            print(f"✅ Saved to database for user: {user.username}")
        else:
            print(f"❌ No user found with ID 1")
        db.close()

        # Test API call with access token
        kite.set_access_token(data['access_token'])
        profile = kite.profile()
        print(f"✅ API test successful: {profile.get('user_name')}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_with_captured_token()