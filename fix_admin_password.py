#!/usr/bin/env python3
"""
Fix admin user password in production database
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from models import User, UserRole

# Production database URL
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:kwCLLsrJOlntnfOeuSATILniOukLMcvS@centerbeam.proxy.rlwy.net:15296/railway"
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def fix_admin_password():
    """Fix the admin password"""
    print("=" * 70)
    print("Fixing Admin Password")
    print("=" * 70)

    # Create engine
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Find admin user
        admin = db.query(User).filter(User.email == "admin@grow-folio.in").first()

        if not admin:
            print("❌ Admin user not found!")
            return

        print(f"✓ Found admin user: {admin.email}")
        print(f"  Current hashed password length: {len(admin.hashed_password) if admin.hashed_password else 0}")

        # Set new password
        new_password = "Growfolio@123"
        print(f"\n  Setting password: {new_password}")
        print(f"  Password length: {len(new_password)} bytes")

        # Hash the password properly
        hashed = pwd_context.hash(new_password)
        print(f"  New hashed password length: {len(hashed)}")

        # Update admin
        admin.hashed_password = hashed
        admin.is_temp_password = False
        admin.is_active = True

        db.commit()

        print("\n✅ Admin password updated successfully!")
        print("\nYou can now login with:")
        print(f"  Email: {admin.email}")
        print(f"  Password: {new_password}")

        # Verify the password works
        print("\nVerifying password...")
        if pwd_context.verify(new_password, hashed):
            print("✅ Password verification successful!")
        else:
            print("❌ Password verification failed!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

    print("=" * 70)

if __name__ == "__main__":
    fix_admin_password()
