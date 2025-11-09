"""
Migration script to create financial planning tables
Creates all tables for financial planning, portfolio design, and product catalog
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from models import Base, FinancialProduct, FinancialPlan, FinancialGoal, PortfolioComponent, RiskProfile, Benchmark, ModelPortfolio
from database import SQLALCHEMY_DATABASE_URL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_tables():
    """Create all financial planning tables"""
    try:
        # Get database URL
        database_url = SQLALCHEMY_DATABASE_URL
        logger.info(f"Connecting to database...")

        # Create engine
        engine = create_engine(database_url)

        # Create all tables
        logger.info("Creating financial planning tables...")
        Base.metadata.create_all(
            bind=engine,
            tables=[
                FinancialProduct.__table__,
                FinancialPlan.__table__,
                FinancialGoal.__table__,
                PortfolioComponent.__table__,
                RiskProfile.__table__,
                Benchmark.__table__,
                ModelPortfolio.__table__
            ],
            checkfirst=True
        )

        logger.info("✅ Successfully created financial planning tables!")
        logger.info("\nTables created:")
        logger.info("  - financial_products (Product catalog: stocks, MF, ETF, bonds)")
        logger.info("  - financial_plans (Main financial planning entity)")
        logger.info("  - financial_goals (Goal-based planning)")
        logger.info("  - portfolio_components (Portfolio investments)")
        logger.info("  - risk_profiles (Risk assessment questionnaire)")
        logger.info("  - benchmarks (Market indices for comparison)")
        logger.info("  - model_portfolios (Pre-built investment baskets)")

        # Verify tables were created
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name IN (
                    'financial_products',
                    'financial_plans',
                    'financial_goals',
                    'portfolio_components',
                    'risk_profiles',
                    'benchmarks',
                    'model_portfolios'
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


def seed_default_data(engine):
    """Seed default data for benchmarks and sample products"""
    try:
        logger.info("\n📦 Seeding default benchmark data...")

        with engine.connect() as conn:
            # Check if benchmarks already exist
            result = conn.execute(text("SELECT COUNT(*) FROM benchmarks"))
            count = result.scalar()

            if count > 0:
                logger.info(f"⏭️  Skipping benchmark seeding - {count} benchmarks already exist")
                return True

            # Insert default Indian market benchmarks
            conn.execute(text("""
                INSERT INTO benchmarks (
                    benchmark_code, benchmark_name, category, description,
                    current_value, return_1y, return_3y, return_5y, last_updated
                ) VALUES
                ('^NSEI', 'Nifty 50', 'Broad Market',
                 'Nifty 50 represents the top 50 large cap companies listed on NSE',
                 22000.00, 18.5, 15.2, 14.8, NOW()),

                ('^BSESN', 'BSE Sensex', 'Broad Market',
                 'BSE Sensex represents 30 of the largest and most actively traded stocks on BSE',
                 73000.00, 18.2, 15.0, 14.5, NOW()),

                ('NIFTYMIDCAP100.NS', 'Nifty Midcap 100', 'Mid Cap',
                 'Nifty Midcap 100 represents mid-sized companies',
                 45000.00, 35.5, 22.3, 18.5, NOW()),

                ('NIFTYSMALLCAP100.NS', 'Nifty Smallcap 100', 'Small Cap',
                 'Nifty Smallcap 100 represents small-sized companies',
                 15000.00, 42.3, 25.8, 20.2, NOW()),

                ('NIFTYIT.NS', 'Nifty IT', 'Sectoral',
                 'Nifty IT represents information technology sector stocks',
                 32000.00, 15.2, 18.5, 20.3, NOW()),

                ('NIFTYBANK.NS', 'Nifty Bank', 'Sectoral',
                 'Nifty Bank represents banking sector stocks',
                 47000.00, 12.5, 10.8, 11.2, NOW()),

                ('NIFTYAUTO.NS', 'Nifty Auto', 'Sectoral',
                 'Nifty Auto represents automobile sector stocks',
                 19000.00, 28.5, 20.2, 16.5, NOW()),

                ('NIFTYPHARMA.NS', 'Nifty Pharma', 'Sectoral',
                 'Nifty Pharma represents pharmaceutical sector stocks',
                 18000.00, 22.3, 15.5, 14.2, NOW()),

                ('NIFTYFMCG.NS', 'Nifty FMCG', 'Sectoral',
                 'Nifty FMCG represents fast-moving consumer goods sector stocks',
                 50000.00, 16.8, 12.5, 13.8, NOW()),

                ('NIFTYENERGY.NS', 'Nifty Energy', 'Sectoral',
                 'Nifty Energy represents energy sector stocks',
                 28000.00, 25.2, 18.5, 15.2, NOW())
            """))

            logger.info("✅ Successfully seeded 10 benchmark indices")

        return True

    except Exception as e:
        logger.error(f"❌ Error seeding default data: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info("FINANCIAL PLANNING DATABASE MIGRATION")
    logger.info("=" * 70)

    # Create tables
    success = create_tables()

    if success:
        # Seed default data
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        seed_default_data(engine)

        logger.info("\n" + "=" * 70)
        logger.info("✅ MIGRATION COMPLETED SUCCESSFULLY!")
        logger.info("=" * 70)
        logger.info("\nNext steps:")
        logger.info("1. Build product catalog with NSE/BSE stocks")
        logger.info("2. Implement NSE/BSE API integration")
        logger.info("3. Create risk profiling questionnaire")
        logger.info("4. Build goal-based planning engine")
        logger.info("5. Create live portfolio designer interface")
    else:
        logger.error("\n" + "=" * 70)
        logger.error("❌ MIGRATION FAILED!")
        logger.error("=" * 70)
        sys.exit(1)
