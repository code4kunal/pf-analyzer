from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import uvicorn
import logging

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

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Start scheduler for daily updates
start_scheduler()

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

# Performance API
@app.get("/api/performance", response_model=schemas.PerformanceMetrics)
async def get_performance(
    period: str = "ALL",
    db: Session = Depends(get_db)
):
    calculator = PerformanceCalculator(db, user_id=1)  # In production, use current user
    metrics = calculator.calculate_portfolio_metrics(period)

    return schemas.PerformanceMetrics(**metrics)

@app.get("/api/statistics")
async def get_statistics(db: Session = Depends(get_db)):
    calculator = PerformanceCalculator(db, user_id=1)  # In production, use current user
    stats = calculator.get_trade_statistics()

    return stats

# Kite Integration API
@app.get("/api/kite/login-url")
async def get_kite_login_url():
    return {"url": kite_service.get_login_url()}

@app.get("/api/kite/callback")
async def kite_callback(
    request_token: str = None,
    status: str = None,
    db: Session = Depends(get_db)
):
    """Handle Kite redirect after authentication"""
    if status == "cancelled" or not request_token:
        return RedirectResponse(url="/settings?error=cancelled")

    try:
        # Generate session with request token
        session_data = kite_service.generate_session(request_token)

        if session_data:
            # Update user's Kite credentials
            user = db.query(User).filter(User.id == 1).first()  # In production, use current user
            if user:
                user.kite_user_id = session_data.get("user_id")
                user.kite_access_token = session_data.get("access_token")
                user.kite_refresh_token = session_data.get("refresh_token")
                db.commit()

            return RedirectResponse(url="/settings?success=true")
        else:
            return RedirectResponse(url="/settings?error=auth_failed")
    except Exception as e:
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

        db.commit()

    return {"message": "Portfolio synced successfully"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)