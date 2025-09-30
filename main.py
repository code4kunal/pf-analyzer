from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import uvicorn
import logging
import os

from database import engine, get_db
from models import Base, User, Trade, JournalEntry, Holding
import schemas
import auth
from kite_integration import kite_service
from performance_calculator import PerformanceCalculator
from scheduler import start_scheduler

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(title="Portfolio Analyzer", version="1.0.0")

@app.on_event("startup")
async def startup_event():
    """Initialize database with default user on startup"""
    try:
        from database import SessionLocal
        db = SessionLocal()

        # Check if we need to create the default user
        existing_user = db.query(User).filter(User.id == 1).first()

        if not existing_user:
            logger.info("Creating default user for production...")

            # Create default user for production
            default_user = User(
                id=1,
                username="testuser",
                email="test@example.com",
                hashed_password="dummy_hash_production",  # Bypass bcrypt for production
                is_active=True
            )

            db.add(default_user)
            db.commit()

            logger.info("✅ Default user created successfully for production")
        else:
            logger.info(f"✅ Default user already exists: {existing_user.username}")

        db.close()

    except Exception as e:
        logger.error(f"❌ Error initializing database: {e}")
        # Don't fail startup if user creation fails
        pass

# Create directories if they don't exist
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)
os.makedirs("templates", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Start scheduler for daily updates (optional, won't crash if fails)
try:
    start_scheduler()
    logger.info("Scheduler started successfully")
except Exception as e:
    logger.warning(f"Could not start scheduler: {e}")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Portfolio Analyzer"}

@app.post("/api/init-user")
async def init_user(db: Session = Depends(get_db)):
    """Initialize a default user for production (temporary endpoint)"""
    try:
        # Check if user exists
        existing_user = db.query(User).filter(User.id == 1).first()
        if existing_user:
            return {"message": "User already exists", "username": existing_user.username, "id": existing_user.id}

        # Create user with direct SQL to avoid bcrypt issues
        from sqlalchemy import text
        db.execute(text("""
            INSERT INTO users (username, email, hashed_password, is_active)
            VALUES ('portfoliouser', 'portfolio@example.com', 'dummy_hash', 1)
        """))
        db.commit()

        # Verify creation
        user = db.query(User).filter(User.username == "portfoliouser").first()
        if user:
            logger.info(f"✅ Created production user: {user.username} (ID: {user.id})")
            return {"message": "User created successfully", "username": user.username, "id": user.id}
        else:
            return {"error": "User creation failed"}

    except Exception as e:
        logger.error(f"❌ Error creating production user: {e}")
        db.rollback()
        return {"error": str(e)}

# Root route - redirect to dashboard
@app.get("/")
async def root():
    return RedirectResponse(url="/dashboard")

# Dashboard route
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

# Journal route
@app.get("/journal", response_class=HTMLResponse)
async def journal(request: Request):
    return templates.TemplateResponse("journal.html", {"request": request})

# Settings route
@app.get("/settings", response_class=HTMLResponse)
async def settings(request: Request):
    return templates.TemplateResponse("settings.html", {"request": request})

# API Routes

# Authentication
@app.post("/api/register", response_model=schemas.UserResponse)
async def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    db_user = db.query(User).filter(
        (User.username == user.username) | (User.email == user.email)
    ).first()

    if db_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")

    # Create new user
    hashed_password = auth.get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

@app.post("/api/login")
async def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = auth.authenticate_user(db, user.username, user.password)

    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = auth.create_access_token(data={"sub": db_user.username})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": schemas.UserResponse.from_orm(db_user)
    }

# Get current user from token
async def get_current_user(token: str, db: Session = Depends(get_db)) -> User:
    username = auth.verify_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user

# Trades API
@app.get("/api/trades", response_model=List[schemas.TradeResponse])
async def get_trades(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    # For demo, returning all trades. In production, filter by current user
    trades = db.query(Trade).offset(skip).limit(limit).all()
    return trades

@app.post("/api/trades", response_model=schemas.TradeResponse)
async def create_trade(
    trade: schemas.TradeCreate,
    db: Session = Depends(get_db)
):
    # Calculate total cost
    total_cost = (trade.quantity * trade.price) + trade.brokerage + trade.taxes

    db_trade = Trade(
        user_id=1,  # In production, get from current user
        **trade.dict(),
        total_cost=total_cost
    )
    db.add(db_trade)
    db.commit()
    db.refresh(db_trade)

    return db_trade

@app.put("/api/trades/{trade_id}", response_model=schemas.TradeResponse)
async def update_trade(
    trade_id: int,
    trade: schemas.TradeUpdate,
    db: Session = Depends(get_db)
):
    db_trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not db_trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    for key, value in trade.dict(exclude_unset=True).items():
        setattr(db_trade, key, value)

    db.commit()
    db.refresh(db_trade)

    return db_trade

@app.delete("/api/trades/{trade_id}")
async def delete_trade(trade_id: int, db: Session = Depends(get_db)):
    db_trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not db_trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    db.delete(db_trade)
    db.commit()

    return {"message": "Trade deleted successfully"}

# Journal API
@app.get("/api/journal", response_model=List[schemas.JournalResponse])
async def get_journal_entries(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    entries = db.query(JournalEntry).offset(skip).limit(limit).all()
    return entries

@app.post("/api/journal", response_model=schemas.JournalResponse)
async def create_journal_entry(
    entry: schemas.JournalCreate,
    db: Session = Depends(get_db)
):
    db_entry = JournalEntry(
        user_id=1,  # In production, get from current user
        **entry.dict()
    )
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)

    return db_entry

@app.put("/api/journal/{entry_id}", response_model=schemas.JournalResponse)
async def update_journal_entry(
    entry_id: int,
    entry: schemas.JournalUpdate,
    db: Session = Depends(get_db)
):
    db_entry = db.query(JournalEntry).filter(JournalEntry.id == entry_id).first()
    if not db_entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    for key, value in entry.dict(exclude_unset=True).items():
        setattr(db_entry, key, value)

    db.commit()
    db.refresh(db_entry)

    return db_entry

# Holdings API
@app.get("/api/holdings", response_model=List[schemas.HoldingResponse])
async def get_holdings(db: Session = Depends(get_db)):
    holdings = db.query(Holding).filter(Holding.user_id == 1).all()  # In production, filter by current user
    return holdings

# Get current positions (intraday and pending settlement)
@app.get("/api/positions")
async def get_positions(db: Session = Depends(get_db)):
    """Get current positions from Kite (includes today's trades)"""
    user = db.query(User).filter(User.id == 1).first()  # In production, use current user

    if not user or not user.kite_access_token:
        return {"error": "Kite not connected", "day": [], "net": []}

    # Initialize Kite
    kite_service.initialize(user.kite_access_token)

    try:
        positions = kite_service.get_positions()

        if not positions:
            return {"day": [], "net": []}

        # Process positions to add realized P&L for closed positions
        result = {
            "day": [],
            "net": []
        }

        # Process day positions (today's trades)
        if positions.get("day"):
            for pos in positions["day"]:
                position_data = {
                    "symbol": pos.get("tradingsymbol"),
                    "exchange": pos.get("exchange"),
                    "product": pos.get("product"),
                    "quantity": pos.get("quantity", 0),
                    "buy_quantity": pos.get("buy_quantity", 0),
                    "sell_quantity": pos.get("sell_quantity", 0),
                    "buy_price": pos.get("buy_price", 0),
                    "sell_price": pos.get("sell_price", 0),
                    "last_price": pos.get("last_price", 0),
                    "pnl": pos.get("pnl", 0),
                    "unrealized": pos.get("unrealised", 0),
                    "realized": pos.get("realised", 0),
                    "value": pos.get("value", 0),
                    "buy_value": pos.get("buy_value", 0),
                    "sell_value": pos.get("sell_value", 0),
                    "is_closed": pos.get("quantity", 0) == 0  # Position is closed if quantity is 0
                }
                result["day"].append(position_data)

        # Process net positions (overall positions across days)
        if positions.get("net"):
            for pos in positions["net"]:
                position_data = {
                    "symbol": pos.get("tradingsymbol"),
                    "exchange": pos.get("exchange"),
                    "product": pos.get("product"),
                    "quantity": pos.get("quantity", 0),
                    "overnight_quantity": pos.get("overnight_quantity", 0),
                    "buy_quantity": pos.get("buy_quantity", 0),
                    "sell_quantity": pos.get("sell_quantity", 0),
                    "buy_price": pos.get("buy_price", 0),
                    "sell_price": pos.get("sell_price", 0),
                    "last_price": pos.get("last_price", 0),
                    "pnl": pos.get("pnl", 0),
                    "unrealized": pos.get("unrealised", 0),
                    "realized": pos.get("realised", 0),
                    "value": pos.get("value", 0),
                    "buy_value": pos.get("buy_value", 0),
                    "sell_value": pos.get("sell_value", 0),
                    "is_closed": pos.get("quantity", 0) == 0  # Position is closed if quantity is 0
                }
                result["net"].append(position_data)

        # Calculate total P&L
        total_realized = sum(pos.get("realized", 0) for pos in result["day"])
        total_unrealized = sum(pos.get("unrealized", 0) for pos in result["day"])

        result["summary"] = {
            "total_pnl": total_realized + total_unrealized,
            "realized_pnl": total_realized,
            "unrealized_pnl": total_unrealized,
            "open_positions": sum(1 for pos in result["day"] if not pos["is_closed"]),
            "closed_positions": sum(1 for pos in result["day"] if pos["is_closed"])
        }

        return result

    except Exception as e:
        logger.error(f"Error fetching positions: {e}")
        return {"error": str(e), "day": [], "net": []}

# Get current orders
@app.get("/api/orders")
async def get_orders(db: Session = Depends(get_db)):
    """Get today's orders from Kite"""
    user = db.query(User).filter(User.id == 1).first()  # In production, use current user

    if not user or not user.kite_access_token:
        return []

    # Initialize Kite
    kite_service.initialize(user.kite_access_token)

    try:
        orders = kite_service.get_orders()

        if not orders:
            return []

        # Process and format orders
        processed_orders = []
        for order in orders:
            processed_orders.append({
                "order_id": order.get("order_id"),
                "exchange_order_id": order.get("exchange_order_id"),
                "symbol": order.get("tradingsymbol"),
                "exchange": order.get("exchange"),
                "transaction_type": order.get("transaction_type"),
                "order_type": order.get("order_type"),
                "product": order.get("product"),
                "quantity": order.get("quantity", 0),
                "filled_quantity": order.get("filled_quantity", 0),
                "pending_quantity": order.get("pending_quantity", 0),
                "price": order.get("price", 0),
                "trigger_price": order.get("trigger_price", 0),
                "average_price": order.get("average_price", 0),
                "status": order.get("status"),
                "status_message": order.get("status_message"),
                "order_timestamp": order.get("order_timestamp"),
                "exchange_timestamp": order.get("exchange_timestamp"),
                "tag": order.get("tag")
            })

        return processed_orders

    except Exception as e:
        logger.error(f"Error fetching orders: {e}")
        return []

# Performance API
@app.get("/api/performance", response_model=schemas.PerformanceMetrics)
async def get_performance(
    period: str = "ALL",
    db: Session = Depends(get_db)
):
    calculator = PerformanceCalculator(db, user_id=1)  # In production, use current user
    metrics = calculator.calculate_portfolio_metrics(period)

    # Enhanced logic to include today's P&L from multiple sources
    today_realized = 0
    today_unrealized = 0

    # Try to get today's P&L from Kite positions
    user = db.query(User).filter(User.id == 1).first()
    if user and user.kite_access_token:
        kite_service.initialize(user.kite_access_token)
        try:
            positions = kite_service.get_positions()
            if positions and positions.get("day"):
                # Calculate today's P&L from positions
                today_realized = sum(pos.get("realised", 0) for pos in positions["day"])
                today_unrealized = sum(pos.get("unrealised", 0) for pos in positions["day"])

                # Also check for closed positions (quantity = 0 but has P&L)
                closed_positions = []
                for pos in positions["day"]:
                    if pos.get("quantity", 0) == 0 and pos.get("realised", 0) != 0:
                        # This is a squared-off position with realized P&L
                        closed_positions.append({
                            "symbol": pos.get("tradingsymbol"),
                            "pnl": pos.get("realised", 0)
                        })
                        logger.info(f"Found closed position: {pos.get('tradingsymbol')} P&L: {pos.get('realised', 0)}")

                if closed_positions:
                    logger.info(f"Total closed positions found: {len(closed_positions)}")

            logger.info(f"Live positions P&L - Realized: {today_realized}, Unrealized: {today_unrealized}")
        except Exception as e:
            logger.warning(f"Failed to fetch today's positions for performance: {e}")

    # Fallback: Check for today's trades in database (from recent syncs)
    from datetime import date
    today = date.today()
    today_trades = db.query(Trade).filter(
        Trade.user_id == 1,
        Trade.trade_date >= today
    ).all()

    if today_trades:
        # Calculate P&L from today's stored trades
        buy_total = sum(t.total_cost for t in today_trades if t.trade_type == TradeType.BUY)
        sell_total = sum(t.quantity * t.price - t.brokerage - t.taxes
                        for t in today_trades if t.trade_type == TradeType.SELL)
        stored_pnl = sell_total - buy_total

        # Use stored P&L if live data isn't available
        if today_realized == 0 and stored_pnl != 0:
            today_realized = stored_pnl
            logger.info(f"Using stored trades P&L for today: {stored_pnl}")

    # Add today's P&L to metrics if we have any
    if today_realized != 0 or today_unrealized != 0:
        metrics["today_pnl"] = today_realized + today_unrealized
        metrics["today_realized"] = today_realized
        metrics["today_unrealized"] = today_unrealized

        # Update total returns to include today's P&L
        original_returns = metrics.get("absolute_returns", 0)
        metrics["absolute_returns"] = original_returns + today_realized + today_unrealized

        # Recalculate percentage returns with today's P&L
        total_investment = metrics.get("total_investment", 0)
        if total_investment > 0:
            metrics["percentage_returns"] = (metrics["absolute_returns"] / total_investment) * 100

        logger.info(f"Enhanced performance with today's P&L - Original: {original_returns}, Today: {today_realized + today_unrealized}, New Total: {metrics['absolute_returns']}")
    else:
        logger.info("No today's P&L data found to add to performance metrics")

    return schemas.PerformanceMetrics(**metrics)

@app.get("/api/statistics")
async def get_statistics(db: Session = Depends(get_db)):
    calculator = PerformanceCalculator(db, user_id=1)  # In production, use current user
    stats = calculator.get_trade_statistics()

    return stats

# Comprehensive Portfolio Summary
@app.get("/api/portfolio-summary")
async def get_portfolio_summary(db: Session = Depends(get_db)):
    """Get complete portfolio summary including holdings, positions, and orders"""
    user = db.query(User).filter(User.id == 1).first()  # In production, use current user

    summary = {
        "holdings": [],
        "positions": {"day": [], "net": []},
        "orders": [],
        "totals": {
            "holdings_value": 0,
            "positions_value": 0,
            "today_pnl": 0,
            "today_realized": 0,
            "today_unrealized": 0,
            "total_investment": 0
        },
        "status": {
            "kite_connected": False,
            "last_sync": None
        }
    }

    # Get holdings from database
    holdings = db.query(Holding).filter(Holding.user_id == 1).all()
    for holding in holdings:
        summary["holdings"].append({
            "symbol": holding.symbol,
            "exchange": holding.exchange,
            "quantity": holding.quantity,
            "average_price": holding.average_price,
            "current_price": holding.current_price,
            "value": holding.quantity * (holding.current_price or holding.average_price),
            "pnl": holding.unrealized_pnl,
            "pnl_percentage": holding.unrealized_pnl_percentage
        })
        summary["totals"]["holdings_value"] += holding.quantity * (holding.current_price or holding.average_price)
        summary["totals"]["total_investment"] += holding.quantity * holding.average_price

    # Get live data from Kite if connected
    if user and user.kite_access_token:
        summary["status"]["kite_connected"] = True
        kite_service.initialize(user.kite_access_token)

        try:
            # Get positions
            positions = kite_service.get_positions()
            if positions:
                # Day positions
                if positions.get("day"):
                    for pos in positions["day"]:
                        pos_data = {
                            "symbol": pos.get("tradingsymbol"),
                            "exchange": pos.get("exchange"),
                            "quantity": pos.get("quantity", 0),
                            "buy_price": pos.get("buy_price", 0),
                            "sell_price": pos.get("sell_price", 0),
                            "last_price": pos.get("last_price", 0),
                            "pnl": pos.get("pnl", 0),
                            "realized": pos.get("realised", 0),
                            "unrealized": pos.get("unrealised", 0),
                            "is_closed": pos.get("quantity", 0) == 0
                        }
                        summary["positions"]["day"].append(pos_data)

                        # Add to totals
                        summary["totals"]["today_realized"] += pos.get("realised", 0)
                        summary["totals"]["today_unrealized"] += pos.get("unrealised", 0)
                        if pos.get("quantity", 0) != 0:
                            summary["totals"]["positions_value"] += pos.get("value", 0)

                # Net positions
                if positions.get("net"):
                    for pos in positions["net"]:
                        if pos.get("quantity", 0) != 0:  # Only show open positions
                            summary["positions"]["net"].append({
                                "symbol": pos.get("tradingsymbol"),
                                "exchange": pos.get("exchange"),
                                "quantity": pos.get("quantity", 0),
                                "average_price": pos.get("average_price", 0),
                                "last_price": pos.get("last_price", 0),
                                "pnl": pos.get("pnl", 0)
                            })

            # Get orders
            orders = kite_service.get_orders()
            if orders:
                # Only show today's orders
                today_orders = []
                for order in orders:
                    order_time = order.get("order_timestamp")
                    if order_time and datetime.now().date() == datetime.fromisoformat(order_time.replace("Z", "+00:00")).date():
                        today_orders.append({
                            "order_id": order.get("order_id"),
                            "symbol": order.get("tradingsymbol"),
                            "transaction_type": order.get("transaction_type"),
                            "quantity": order.get("quantity"),
                            "price": order.get("price"),
                            "status": order.get("status"),
                            "order_time": order_time
                        })
                summary["orders"] = today_orders

            summary["totals"]["today_pnl"] = summary["totals"]["today_realized"] + summary["totals"]["today_unrealized"]

        except Exception as e:
            logger.error(f"Error fetching live data: {e}")
            summary["status"]["error"] = str(e)

    # Calculate total portfolio value
    summary["totals"]["total_value"] = summary["totals"]["holdings_value"] + summary["totals"]["positions_value"]

    return summary

# Test endpoint to simulate squared off positions
@app.get("/api/test-squared-positions")
async def test_squared_positions():
    """Simulate what squared off positions would look like"""
    return {
        "day": [
            {
                "symbol": "RELIANCE",
                "exchange": "NSE",
                "quantity": 0,  # Squared off
                "buy_quantity": 10,
                "sell_quantity": 10,
                "buy_price": 2450.50,
                "sell_price": 2465.25,
                "last_price": 2465.25,
                "pnl": 147.50,  # (2465.25 - 2450.50) * 10
                "realized": 147.50,
                "unrealized": 0,
                "value": 0,
                "buy_value": 24505.00,
                "sell_value": 24652.50,
                "is_closed": True
            },
            {
                "symbol": "TCS",
                "exchange": "NSE",
                "quantity": 0,  # Squared off
                "buy_quantity": 5,
                "sell_quantity": 5,
                "buy_price": 3680.75,
                "sell_price": 3695.20,
                "last_price": 3695.20,
                "pnl": 72.25,  # (3695.20 - 3680.75) * 5
                "realized": 72.25,
                "unrealized": 0,
                "value": 0,
                "buy_value": 18403.75,
                "sell_value": 18476.00,
                "is_closed": True
            },
            {
                "symbol": "HDFCBANK",
                "exchange": "NSE",
                "quantity": 3,  # Still open
                "buy_quantity": 3,
                "sell_quantity": 0,
                "buy_price": 1720.30,
                "sell_price": 0,
                "last_price": 1735.50,
                "pnl": 45.60,  # (1735.50 - 1720.30) * 3
                "realized": 0,
                "unrealized": 45.60,
                "value": 5206.50,
                "buy_value": 5160.90,
                "sell_value": 0,
                "is_closed": False
            }
        ],
        "summary": {
            "total_pnl": 265.35,  # 147.50 + 72.25 + 45.60
            "realized_pnl": 219.75,  # 147.50 + 72.25
            "unrealized_pnl": 45.60,
            "open_positions": 1,
            "closed_positions": 2
        }
    }

# Kite Integration API
@app.get("/api/kite/login-url")
async def get_kite_login_url():
    return {"url": kite_service.get_login_url()}

@app.get("/api/kite/status")
async def get_kite_status(db: Session = Depends(get_db)):
    """Check if Kite is connected"""
    user = db.query(User).filter(User.id == 1).first()  # In production, use current user

    if user and user.kite_access_token:
        return {
            "connected": True,
            "user_id": user.kite_user_id,
            "message": f"Connected as {user.kite_user_id}"
        }
    else:
        return {
            "connected": False,
            "user_id": None,
            "message": "Not connected to Zerodha Kite"
        }

@app.get("/api/kite/callback")
async def kite_callback(
    request_token: str = None,
    status: str = None,
    db: Session = Depends(get_db)
):
    """Handle Kite redirect after authentication"""
    logger.info(f"🔍 Kite callback received - Token: {request_token}, Status: {status}")

    if status == "cancelled" or not request_token:
        logger.warning(f"❌ Callback cancelled or no token")
        return RedirectResponse(url="/settings?error=cancelled")

    try:
        logger.info(f"📞 Attempting to generate session with token: {request_token}")
        # Generate session with request token
        session_data = kite_service.generate_session(request_token)

        if session_data:
            logger.info(f"✅ Session generated successfully for user: {session_data.get('user_id')}")
            # Update user's Kite credentials
            user = db.query(User).filter(User.id == 1).first()  # In production, use current user
            if user:
                user.kite_user_id = session_data.get("user_id")
                user.kite_access_token = session_data.get("access_token")
                user.kite_refresh_token = session_data.get("refresh_token")
                db.commit()
                logger.info(f"✅ Saved credentials to database for user: {user.username}")
            else:
                logger.error(f"❌ No user found with ID 1")

            return RedirectResponse(url="/settings?success=true")
        else:
            logger.error(f"❌ Failed to generate session data")
            return RedirectResponse(url="/settings?error=auth_failed")
    except Exception as e:
        logger.error(f"❌ Callback error: {e}")
        return RedirectResponse(url=f"/settings?error={str(e)}")

@app.post("/api/kite/postback")
async def kite_postback(request: Request):
    """Handle Kite postback for order updates"""
    try:
        data = await request.json()
        # Log the postback data for order updates
        logger.info(f"Kite postback received: {data}")
        # Process order updates here if needed
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error processing Kite postback: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/kite/authorize", response_model=schemas.KiteAuthResponse)
async def authorize_kite(
    auth_request: schemas.KiteAuthRequest,
    db: Session = Depends(get_db)
):
    session_data = kite_service.generate_session(auth_request.request_token)

    if not session_data:
        return schemas.KiteAuthResponse(
            success=False,
            message="Failed to authorize with Kite"
        )

    # Update user's Kite credentials
    user = db.query(User).filter(User.id == 1).first()  # In production, use current user
    if user:
        user.kite_user_id = session_data.get("user_id")
        user.kite_access_token = session_data.get("access_token")
        user.kite_refresh_token = session_data.get("refresh_token")
        db.commit()

    return schemas.KiteAuthResponse(
        success=True,
        message="Successfully authorized with Kite",
        user_id=session_data.get("user_id")
    )

@app.get("/api/kite/sync")
async def sync_portfolio(db: Session = Depends(get_db)):
    """Sync portfolio with Kite"""
    user = db.query(User).filter(User.id == 1).first()  # In production, use current user

    if not user or not user.kite_access_token:
        raise HTTPException(status_code=400, detail="Kite not connected")

    # Initialize Kite with user's access token
    kite_service.initialize(user.kite_access_token)

    # Sync holdings
    kite_holdings = kite_service.get_holdings()
    if kite_holdings:
        # Clear existing holdings
        db.query(Holding).filter(Holding.user_id == user.id).delete()

        # Add new holdings
        for kh in kite_holdings:
            holding = Holding(
                user_id=user.id,
                symbol=kh["tradingsymbol"],
                exchange=kh["exchange"],
                quantity=kh["quantity"],
                average_price=kh["average_price"],
                current_price=kh["last_price"],
                unrealized_pnl=kh["pnl"],
                unrealized_pnl_percentage=(kh["pnl"] / (kh["average_price"] * kh["quantity"]) * 100) if kh["quantity"] > 0 else 0
            )
            db.add(holding)

        db.commit()

    # Sync today's trades
    kite_trades = kite_service.get_trades()
    trades_synced = 0
    if kite_trades:
        for kt in kite_trades:
            # Check if trade already exists
            existing_trade = db.query(Trade).filter(
                Trade.zerodha_trade_id == kt["trade_id"]
            ).first()

            if not existing_trade:
                trade = Trade(
                    user_id=user.id,
                    symbol=kt["tradingsymbol"],
                    exchange=kt["exchange"],
                    trade_type="BUY" if kt["transaction_type"] == "BUY" else "SELL",
                    order_type=kt.get("order_type", "MARKET"),
                    quantity=kt["quantity"],
                    price=kt["average_price"],
                    brokerage=0,  # Would need to calculate
                    taxes=0,  # Would need to calculate
                    total_cost=kt["quantity"] * kt["average_price"],
                    trade_date=datetime.now(),
                    zerodha_order_id=kt.get("order_id"),
                    zerodha_trade_id=kt["trade_id"]
                )
                db.add(trade)
                trades_synced += 1

        db.commit()

    # Get today's positions (includes intraday and pending settlements)
    positions = kite_service.get_positions()
    positions_info = ""
    closed_positions_synced = 0

    if positions and "day" in positions:
        day_positions = positions["day"]
        if day_positions:
            positions_info = f" Found {len(day_positions)} day positions."

            # Check for closed positions and save their realized P&L
            for pos in day_positions:
                if pos.get("quantity", 0) == 0 and pos.get("realised", 0) != 0:
                    # This is a closed position with realized P&L
                    # Check if we already have this as a trade pair
                    existing_closed_trade = db.query(Trade).filter(
                        Trade.user_id == user.id,
                        Trade.symbol == pos.get("tradingsymbol"),
                        Trade.trade_date >= datetime.now().date()
                    ).first()

                    if not existing_closed_trade and pos.get("sell_quantity", 0) > 0:
                        # Save the closed position as a completed trade
                        # Create both buy and sell records for complete tracking

                        # Buy trade
                        if pos.get("buy_quantity", 0) > 0:
                            buy_trade = Trade(
                                user_id=user.id,
                                symbol=pos.get("tradingsymbol"),
                                exchange=pos.get("exchange"),
                                trade_type="BUY",
                                order_type="MARKET",
                                quantity=pos.get("buy_quantity"),
                                price=pos.get("buy_price", 0),
                                total_cost=pos.get("buy_value", 0),
                                trade_date=datetime.now()
                            )
                            db.add(buy_trade)

                        # Sell trade
                        if pos.get("sell_quantity", 0) > 0:
                            sell_trade = Trade(
                                user_id=user.id,
                                symbol=pos.get("tradingsymbol"),
                                exchange=pos.get("exchange"),
                                trade_type="SELL",
                                order_type="MARKET",
                                quantity=pos.get("sell_quantity"),
                                price=pos.get("sell_price", 0),
                                total_cost=pos.get("sell_value", 0),
                                actual_exit_price=pos.get("sell_price", 0),
                                trade_date=datetime.now()
                            )
                            db.add(sell_trade)

                        closed_positions_synced += 1

            db.commit()

    holdings_synced = len(kite_holdings) if kite_holdings else 0

    return {
        "message": f"Portfolio synced successfully. Holdings: {holdings_synced}, Trades: {trades_synced}, Closed Positions: {closed_positions_synced}.{positions_info}",
        "details": {
            "holdings_synced": holdings_synced,
            "trades_synced": trades_synced,
            "closed_positions_synced": closed_positions_synced,
            "positions_available": bool(positions and positions.get("day")),
            "note": "Today's buy orders will appear in holdings tomorrow (T+1 settlement)"
        }
    }

# Debug endpoint to check raw Kite data
@app.get("/api/debug/kite-raw")
async def debug_kite_raw(db: Session = Depends(get_db)):
    """Debug endpoint to see raw Kite API responses"""
    user = db.query(User).filter(User.id == 1).first()

    if not user or not user.kite_access_token:
        return {"error": "Kite not connected"}

    # Initialize Kite
    kite_service.initialize(user.kite_access_token)

    try:
        # Get raw data from Kite APIs
        raw_holdings = kite_service.get_holdings()
        raw_trades = kite_service.get_trades()
        raw_positions = kite_service.get_positions()  # This might show today's positions

        return {
            "holdings_count": len(raw_holdings) if raw_holdings else 0,
            "holdings_sample": raw_holdings[:2] if raw_holdings else [],
            "trades_count": len(raw_trades) if raw_trades else 0,
            "trades_sample": raw_trades[:2] if raw_trades else [],
            "positions": raw_positions if raw_positions else {},
            "debug_info": {
                "user_id": user.kite_user_id,
                "access_token_exists": bool(user.kite_access_token),
                "kite_service_initialized": bool(kite_service.kite)
            }
        }
    except Exception as e:
        return {"error": str(e), "debug_info": "Failed to fetch Kite data"}

# Test endpoint to demonstrate performance with today's P&L
@app.get("/api/test-performance-with-pnl")
async def test_performance_with_pnl(db: Session = Depends(get_db)):
    """Demo endpoint showing how performance would look with today's realized P&L"""
    calculator = PerformanceCalculator(db, user_id=1)
    metrics = calculator.calculate_portfolio_metrics("ALL")

    # Simulate today's trading data
    simulated_realized = 219.75  # From test squared positions
    simulated_unrealized = 45.60  # From open position

    # Add simulated today's P&L to metrics
    metrics["today_pnl"] = simulated_realized + simulated_unrealized
    metrics["today_realized"] = simulated_realized
    metrics["today_unrealized"] = simulated_unrealized

    # Update total returns to include today's P&L
    original_returns = metrics.get("absolute_returns", 0)
    metrics["absolute_returns"] = original_returns + simulated_realized + simulated_unrealized

    # Recalculate percentage returns if we have investment
    total_investment = metrics.get("total_investment", 0)
    if total_investment == 0:
        # For demo purposes, assume some investment
        total_investment = 50000  # Assume 50k investment
        metrics["total_investment"] = total_investment
        metrics["current_value"] = total_investment + metrics["absolute_returns"]

    if total_investment > 0:
        metrics["percentage_returns"] = (metrics["absolute_returns"] / total_investment) * 100

    return {
        **metrics,
        "note": "This demo shows how performance would look with today's P&L included",
        "demo_data": {
            "original_returns": original_returns,
            "todays_pnl": simulated_realized + simulated_unrealized,
            "new_total_returns": metrics["absolute_returns"]
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)