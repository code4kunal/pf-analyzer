#!/usr/bin/env python3
"""
Create a test user for debugging
"""
from database import SessionLocal
from models import User
from auth import get_password_hash

def create_test_user():
    db = SessionLocal()
    try:
        # Check if user exists
        existing_user = db.query(User).filter(User.username == "testuser").first()
        if existing_user:
            print(f"✅ User already exists: {existing_user.username} (ID: {existing_user.id})")
            return existing_user

        # Create test user
        hashed_password = get_password_hash("testpass123")
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=hashed_password
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        print(f"✅ Created test user: {user.username} (ID: {user.id})")
        return user

    except Exception as e:
        print(f"❌ Error creating user: {e}")
        db.rollback()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()