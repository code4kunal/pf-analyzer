#!/usr/bin/env python3
"""
Setup Production Database on Railway
- Creates all database tables
- Creates admin user
"""

import os
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# Import all models to ensure they're registered
from models import Base, User, UserRole

# Production database URL
DATABASE_URL = "postgresql://postgres:kwCLLsrJOlntnfOeuSATILniOukLMcvS@centerbeam.proxy.rlwy.net:15296/railway"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def setup_database():
    """Create all tables and admin user"""

    print("=" * 70)
    print("Setting up Production Database on Railway")
    print("=" * 70)

    # Create engine
    print("\n1. Connecting to Railway PostgreSQL...")
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300
    )

    try:
        # Test connection
        with engine.connect() as conn:
            print("✅ Connected successfully!")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return

    # Create all tables
    print("\n2. Creating database schema (all tables)...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database schema created!")

        # List created tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"\n   Tables created ({len(tables)}):")
        for table in sorted(tables):
            print(f"   - {table}")
    except Exception as e:
        print(f"❌ Failed to create schema: {e}")
        return

    # Create admin user
    print("\n3. Creating admin user...")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Check if admin already exists
        existing_admin = db.query(User).filter(User.email == "admin@grow-folio.in").first()

        if existing_admin:
            print("⚠️  Admin user already exists!")
            print(f"   Email: {existing_admin.email}")
            print(f"   Name: {existing_admin.full_name}")
            print(f"   Role: {existing_admin.role}")
        else:
            # Create admin user
            admin_password = "Growfolio@123"
            hashed_password = pwd_context.hash(admin_password)

            admin_user = User(
                email="admin@grow-folio.in",
                full_name="Admin User",
                phone="+91 9876543210",
                role=UserRole.ADMIN,
                hashed_password=hashed_password,
                is_active=True,
                is_temp_password=False  # Set to False so no forced password change
            )

            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)

            print("✅ Admin user created!")
            print(f"\n   Email: {admin_user.email}")
            print(f"   Password: {admin_password}")
            print(f"   Role: {admin_user.role}")
            print(f"   ID: {admin_user.id}")

    except Exception as e:
        print(f"❌ Failed to create admin user: {e}")
        db.rollback()
    finally:
        db.close()

    # Verify setup
    print("\n4. Verifying setup...")
    db = SessionLocal()
    try:
        user_count = db.query(User).count()
        admin_count = db.query(User).filter(User.role == UserRole.ADMIN).count()

        print(f"✅ Total users: {user_count}")
        print(f"✅ Admin users: {admin_count}")
    except Exception as e:
        print(f"⚠️  Could not verify: {e}")
    finally:
        db.close()

    print("\n" + "=" * 70)
    print("✅ Production Database Setup Complete!")
    print("=" * 70)
    print("\nYou can now login at: https://cms.grow-folio.in")
    print("Email: admin@grow-folio.in")
    print("Password: Growfolio@123")
    print("\n⚠️  Please change the password after first login!")
    print("=" * 70)

if __name__ == "__main__":
    setup_database()
