"""
Database Reset Script for GrowFolio CMS
This script will:
1. Drop all existing tables from the old Portfolio Analyzer
2. Create new tables for GrowFolio CMS
"""

from sqlalchemy import inspect, text
from database import engine, Base
from models import *  # Import all models to register them with Base
import sys
import argparse

def confirm_reset():
    """Ask for user confirmation before resetting database"""
    print("⚠️  WARNING: This will DROP ALL EXISTING TABLES and create new ones!")
    print("⚠️  All data will be PERMANENTLY DELETED!")
    print()
    response = input("Are you sure you want to continue? (type 'YES' to confirm): ")
    return response == "YES"

def drop_all_tables():
    """Drop all existing tables"""
    print("\n🗑️  Dropping all existing tables...")

    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    if not existing_tables:
        print("   No existing tables found.")
        return

    print(f"   Found {len(existing_tables)} tables to drop:")
    for table in existing_tables:
        print(f"   - {table}")

    # Drop all tables using Base.metadata
    Base.metadata.drop_all(bind=engine)
    print("   ✅ All tables dropped successfully")

def create_all_tables():
    """Create all new tables for GrowFolio CMS"""
    print("\n🏗️  Creating new tables for GrowFolio CMS...")

    # Create all tables defined in models
    Base.metadata.create_all(bind=engine)

    # List created tables
    inspector = inspect(engine)
    created_tables = inspector.get_table_names()

    print(f"   Created {len(created_tables)} tables:")
    for table in created_tables:
        print(f"   - {table}")

    print("   ✅ All tables created successfully")

def create_default_admin():
    """Create a default admin user"""
    from sqlalchemy.orm import Session
    from passlib.context import CryptContext

    print("\n👤 Creating default admin user...")

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    with Session(engine) as session:
        # Check if admin already exists
        admin = session.query(User).filter(User.email == "admin@grow-folio.in").first()
        if admin:
            print("   ⚠️  Admin user already exists")
            return

        # Create admin user
        admin = User(
            email="admin@grow-folio.in",
            hashed_password=pwd_context.hash("Admin@123"),
            full_name="Admin User",
            role=UserRole.ADMIN,
            is_active=True,
            is_temp_password=True,
            phone=None
        )
        session.add(admin)
        session.commit()

        print("   ✅ Admin user created:")
        print(f"      Email: admin@grow-folio.in")
        print(f"      Password: Admin@123")
        print(f"      ⚠️  Please change this password after first login!")

def main():
    parser = argparse.ArgumentParser(description='Reset GrowFolio CMS database')
    parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation prompt')
    args = parser.parse_args()

    print("=" * 60)
    print("GrowFolio CMS - Database Reset")
    print("=" * 60)

    # Confirm before proceeding (skip if --yes flag is used)
    if not args.yes and not confirm_reset():
        print("\n❌ Database reset cancelled.")
        sys.exit(0)

    try:
        # Step 1: Drop all existing tables
        drop_all_tables()

        # Step 2: Create new tables
        create_all_tables()

        # Step 3: Create default admin user
        create_default_admin()

        print("\n" + "=" * 60)
        print("✅ Database reset completed successfully!")
        print("=" * 60)
        print("\n📋 Next steps:")
        print("1. Start the application: uvicorn main:app --reload")
        print("2. Login with admin credentials above")
        print("3. Change the default admin password")
        print("4. Start creating users and customers")
        print()

    except Exception as e:
        print(f"\n❌ Error during database reset: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
