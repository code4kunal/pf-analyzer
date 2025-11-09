"""
Migration script to create client profiling questionnaire tables
Creates tables for invite links and response storage
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from models import Base, QuestionnaireInvite, ClientProfilingResponse
from database import SQLALCHEMY_DATABASE_URL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_tables():
    """Create questionnaire tables"""
    try:
        logger.info(f"Connecting to database...")

        # Create engine
        engine = create_engine(SQLALCHEMY_DATABASE_URL)

        # Create all tables
        logger.info("Creating questionnaire tables...")
        Base.metadata.create_all(
            bind=engine,
            tables=[
                QuestionnaireInvite.__table__,
                ClientProfilingResponse.__table__
            ],
            checkfirst=True
        )

        logger.info("✅ Successfully created questionnaire tables!")
        logger.info("\nTables created:")
        logger.info("  - questionnaire_invites (Invite link management)")
        logger.info("  - client_profiling_responses (Detailed questionnaire responses)")

        # Verify tables were created
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name IN (
                    'questionnaire_invites',
                    'client_profiling_responses'
                )
                ORDER BY table_name;
            """))

            tables = [row[0] for row in result]
            logger.info(f"\n✅ Verified {len(tables)} tables in database:")
            for table in tables:
                logger.info(f"  - {table}")

        return True

    except Exception as e:
        logger.error(f"❌ Error creating tables: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info("CLIENT PROFILING QUESTIONNAIRE DATABASE MIGRATION")
    logger.info("=" * 70)

    # Create tables
    success = create_tables()

    if success:
        logger.info("\n" + "=" * 70)
        logger.info("✅ MIGRATION COMPLETED SUCCESSFULLY!")
        logger.info("=" * 70)
        logger.info("\nNext steps:")
        logger.info("1. Create questionnaire invite service")
        logger.info("2. Build API endpoints for invite management")
        logger.info("3. Create public questionnaire form")
        logger.info("4. Build admin dashboard for viewing responses")
    else:
        logger.error("\n" + "=" * 70)
        logger.error("❌ MIGRATION FAILED!")
        logger.error("=" * 70)
        sys.exit(1)
