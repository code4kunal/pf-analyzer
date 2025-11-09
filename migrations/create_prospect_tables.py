"""
Create prospect tables using SQLAlchemy
Usage: python migrations/create_prospect_tables.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine, Base
from models import Prospect, ProspectCommunication, ProspectActivity, ImportBatch

def create_tables():
    """Create all prospect-related tables"""
    print("Creating prospect tables...")

    try:
        # This will create only the tables that don't exist yet
        Base.metadata.create_all(bind=engine, checkfirst=True)
        print("✓ Tables created successfully!")
        print("\nCreated tables:")
        print("  - prospects")
        print("  - prospect_communications")
        print("  - prospect_activities")
        print("  - import_batches")

    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        raise

if __name__ == "__main__":
    create_tables()
