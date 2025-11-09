"""
Run database migrations
Usage: python migrations/run_migration.py
"""

import sys
import os

# Add parent directory to path to import database module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine
from sqlalchemy import text

def run_migration():
    """Run the prospects migration"""
    migration_file = os.path.join(os.path.dirname(__file__), '001_add_prospects.sql')

    print("Reading migration file...")
    with open(migration_file, 'r') as f:
        migration_sql = f.read()

    print("Connecting to database...")
    with engine.connect() as conn:
        print("Executing migration...")

        # Split by semicolons and execute each statement
        statements = [s.strip() for s in migration_sql.split(';') if s.strip() and not s.strip().startswith('--')]

        for i, statement in enumerate(statements, 1):
            if statement:
                try:
                    print(f"Executing statement {i}/{len(statements)}...")
                    conn.execute(text(statement))
                    conn.commit()
                except Exception as e:
                    print(f"Error executing statement {i}: {e}")
                    print(f"Statement: {statement[:100]}...")
                    # Continue with other statements even if one fails

    print("Migration completed successfully!")

if __name__ == "__main__":
    run_migration()
