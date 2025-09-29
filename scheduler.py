from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User, PerformanceSnapshot
from kite_integration import kite_service
from performance_calculator import PerformanceCalculator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def update_portfolio_data():
    """Daily task to update portfolio data from Kite"""
    logger.info(f"Starting portfolio update at {datetime.now()}")

    db = SessionLocal()
    try:
        # Get all users with Kite credentials
        users = db.query(User).filter(User.kite_access_token.isnot(None)).all()

        for user in users:
            try:
                # Initialize Kite for this user
                kite_service.initialize(user.kite_access_token)

                # Update holdings
                holdings = kite_service.get_holdings()
                if holdings:
                    # Update logic here
                    logger.info(f"Updated holdings for user {user.username}")

                # Update trades
                trades = kite_service.get_trades()
                if trades:
                    # Update logic here
                    logger.info(f"Updated trades for user {user.username}")

            except Exception as e:
                logger.error(f"Error updating portfolio for user {user.username}: {e}")

    finally:
        db.close()

    logger.info(f"Portfolio update completed at {datetime.now()}")

def calculate_daily_performance():
    """Calculate and store daily performance metrics"""
    logger.info(f"Starting performance calculation at {datetime.now()}")

    db = SessionLocal()
    try:
        users = db.query(User).all()

        for user in users:
            try:
                calculator = PerformanceCalculator(db, user.id)
                metrics = calculator.calculate_portfolio_metrics()

                # Store performance snapshot
                snapshot = PerformanceSnapshot(
                    user_id=user.id,
                    snapshot_date=datetime.now().date(),
                    total_investment=metrics["total_investment"],
                    current_value=metrics["current_value"],
                    absolute_returns=metrics["absolute_returns"],
                    percentage_returns=metrics["percentage_returns"],
                    xirr=metrics["xirr"],
                    cagr=metrics["cagr"],
                    max_drawdown=metrics["max_drawdown"],
                    sharpe_ratio=metrics["sharpe_ratio"],
                    win_rate=metrics["win_rate"],
                    total_trades=metrics["total_trades"],
                    winning_trades=metrics["winning_trades"],
                    losing_trades=metrics["losing_trades"]
                )
                db.add(snapshot)
                db.commit()

                logger.info(f"Performance snapshot created for user {user.username}")

            except Exception as e:
                logger.error(f"Error calculating performance for user {user.username}: {e}")

    finally:
        db.close()

    logger.info(f"Performance calculation completed at {datetime.now()}")

def start_scheduler():
    """Start the background scheduler"""
    # Schedule portfolio update at 9:00 AM every day
    scheduler.add_job(
        update_portfolio_data,
        CronTrigger(hour=9, minute=0),
        id="portfolio_update",
        name="Daily Portfolio Update",
        replace_existing=True
    )

    # Schedule performance calculation at 4:00 PM every day (after market close)
    scheduler.add_job(
        calculate_daily_performance,
        CronTrigger(hour=16, minute=0),
        id="performance_calculation",
        name="Daily Performance Calculation",
        replace_existing=True
    )

    scheduler.start()
    logger.info("Scheduler started successfully")

def stop_scheduler():
    """Stop the background scheduler"""
    scheduler.shutdown()
    logger.info("Scheduler stopped")