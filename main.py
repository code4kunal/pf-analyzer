from fastapi import FastAPI, Depends, HTTPException, Request, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import uvicorn
import logging
import os
import asyncio
import json
from collections import defaultdict

from database import engine, get_db
from models import Base, User, Trade, JournalEntry, Holding, Watchlist, AlertLog
import schemas
import auth
from kite_integration import kite_service
from performance_calculator import PerformanceCalculator
from scheduler import start_scheduler
from notification_service import notification_service

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(title="Portfolio Analyzer", version="1.0.0")

# Create directories if they don't exist
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)
os.makedirs("templates", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions: defaultdict = defaultdict(set)  # symbol -> set of websockets

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            # Remove from all subscriptions
            for symbol in list(self.subscriptions.keys()):
                if websocket in self.subscriptions[symbol]:
                    self.subscriptions[symbol].discard(websocket)
                    if not self.subscriptions[symbol]:
                        del self.subscriptions[symbol]
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    def subscribe(self, websocket: WebSocket, symbol: str):
        self.subscriptions[symbol].add(websocket)
        logger.info(f"WebSocket subscribed to {symbol}")

    def unsubscribe(self, websocket: WebSocket, symbol: str):
        if symbol in self.subscriptions:
            self.subscriptions[symbol].discard(websocket)
            if not self.subscriptions[symbol]:
                del self.subscriptions[symbol]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except:
            self.disconnect(websocket)

    async def broadcast_to_symbol(self, symbol: str, message: dict):
        if symbol in self.subscriptions:
            disconnected = []
            for websocket in self.subscriptions[symbol]:
                try:
                    await websocket.send_text(json.dumps(message))
                except:
                    disconnected.append(websocket)

            # Clean up disconnected websockets
            for ws in disconnected:
                self.disconnect(ws)

manager = ConnectionManager()

# Background task for price updates
async def price_update_task():
    """Background task to fetch and broadcast live prices"""
    while True:
        try:
            if manager.subscriptions and kite_service.kite and kite_service.access_token:
                # Get all subscribed symbols
                symbols = list(manager.subscriptions.keys())
                if symbols:
                    # Fetch quotes for all symbols
                    quotes = kite_service.get_ltp(symbols)

                    if quotes:
                        for symbol, quote_data in quotes.items():
                            price_update = {
                                'type': 'price_update',
                                'symbol': symbol,
                                'price': quote_data.get('last_price'),
                                'timestamp': datetime.now().isoformat()
                            }
                            await manager.broadcast_to_symbol(symbol, price_update)

            # Wait 5 seconds before next update
            await asyncio.sleep(5)

        except Exception as e:
            logger.error(f"Price update task error: {e}")
            await asyncio.sleep(10)  # Wait longer on error

# Background task for SL/Target monitoring
async def alert_monitoring_task():
    """Background task to monitor price alerts and trigger actions"""
    while True:
        try:
            if kite_service.kite and kite_service.access_token:
                # Get database session
                from database import SessionLocal
                db = SessionLocal()

                try:
                    # Get all active watchlist items with alerts enabled
                    watchlist_items = db.query(Watchlist).filter(
                        Watchlist.alert_enabled == True,
                        (Watchlist.target_price.isnot(None) | Watchlist.stop_loss_price.isnot(None))
                    ).all()

                    if watchlist_items:
                        # Get symbols to check
                        symbols = [f"{item.exchange}:{item.symbol}" for item in watchlist_items]
                        quotes = kite_service.get_ltp(symbols)

                        if quotes:
                            for item in watchlist_items:
                                symbol_key = f"{item.exchange}:{item.symbol}"
                                if symbol_key in quotes:
                                    current_price = quotes[symbol_key].get('last_price')

                                    if current_price:
                                        # Check target price alert
                                        if item.target_price and current_price >= item.target_price:
                                            await trigger_price_alert(db, item, current_price, "TARGET_REACHED")

                                        # Check stop loss alert
                                        if item.stop_loss_price and current_price <= item.stop_loss_price:
                                            await trigger_price_alert(db, item, current_price, "STOP_LOSS_TRIGGERED")

                finally:
                    db.close()

            # Wait 30 seconds before next check
            await asyncio.sleep(30)

        except Exception as e:
            logger.error(f"Alert monitoring task error: {e}")
            await asyncio.sleep(60)  # Wait longer on error

async def trigger_price_alert(db: Session, watchlist_item: Watchlist, current_price: float, alert_type: str):
    """Trigger price alert and log it"""
    try:
        # Create alert message
        if alert_type == "TARGET_REACHED":
            message = f"{watchlist_item.symbol} target price ₹{watchlist_item.target_price} reached! Current: ₹{current_price}"
        else:
            message = f"{watchlist_item.symbol} stop loss ₹{watchlist_item.stop_loss_price} triggered! Current: ₹{current_price}"

        # Check if alert was already sent recently (avoid spam)
        recent_alert = db.query(AlertLog).filter(
            AlertLog.watchlist_id == watchlist_item.id,
            AlertLog.alert_type == alert_type,
            AlertLog.created_at >= datetime.now() - timedelta(hours=1)
        ).first()

        if not recent_alert:
            # Create alert log
            alert_log = AlertLog(
                user_id=watchlist_item.user_id,
                watchlist_id=watchlist_item.id,
                symbol=watchlist_item.symbol,
                alert_type=alert_type,
                message=message,
                current_price=current_price,
                trigger_price=watchlist_item.target_price if alert_type == "TARGET_REACHED" else watchlist_item.stop_loss_price
            )
            db.add(alert_log)
            db.commit()

            logger.info(f"🚨 Price Alert: {message}")

            # Broadcast alert to WebSocket clients
            alert_data = {
                'type': 'price_alert',
                'symbol': f"{watchlist_item.exchange}:{watchlist_item.symbol}",
                'alert_type': alert_type,
                'message': message,
                'current_price': current_price,
                'timestamp': datetime.now().isoformat()
            }
            await manager.broadcast_to_symbol(f"{watchlist_item.exchange}:{watchlist_item.symbol}", alert_data)

            # TODO: Send SMS/Email notifications here
            await send_alert_notification(watchlist_item.user_id, message, alert_type)

    except Exception as e:
        logger.error(f"Error triggering price alert: {e}")

async def send_alert_notification(user_id: int, message: str, alert_type: str):
    """Send alert notifications via SMS/Email"""
    try:
        # Get database session
        from database import SessionLocal
        db = SessionLocal()

        try:
            # Get user details
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.error(f"User {user_id} not found for notification")
                return

            # Extract symbol and prices from message for structured notification
            parts = message.split()
            symbol = parts[0] if parts else "Unknown"

            # Try to extract prices from message
            current_price = 0
            trigger_price = 0
            try:
                # Look for ₹ symbols in message
                import re
                prices = re.findall(r'₹([\d.]+)', message)
                if len(prices) >= 2:
                    trigger_price = float(prices[0])
                    current_price = float(prices[1])
                elif len(prices) == 1:
                    current_price = float(prices[0])
            except:
                pass

            # Send notifications based on user preferences
            email_to_send = user.email if user.email_notifications_enabled else None
            phone_to_send = user.phone_number if user.sms_notifications_enabled and user.phone_number else None

            if email_to_send or phone_to_send:
                results = await notification_service.send_price_alert(
                    user_email=email_to_send,
                    user_phone=phone_to_send,
                    symbol=symbol,
                    alert_type=alert_type,
                    current_price=current_price,
                    trigger_price=trigger_price
                )

                # Update alert log with delivery status
                recent_alert = db.query(AlertLog).filter(
                    AlertLog.user_id == user_id,
                    AlertLog.alert_type == alert_type,
                    AlertLog.created_at >= datetime.now() - timedelta(minutes=5)
                ).order_by(AlertLog.created_at.desc()).first()

                if recent_alert:
                    recent_alert.sent_email = results.get('email_sent', False)
                    recent_alert.sent_sms = results.get('sms_sent', False)
                    db.commit()

                logger.info(f"📱 Notifications sent to user {user_id}: Email={results.get('email_sent')}, SMS={results.get('sms_sent')}")
            else:
                logger.info(f"📱 No notification preferences set for user {user_id}")

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error sending notification: {e}")

# Start background tasks
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(price_update_task())
    asyncio.create_task(alert_monitoring_task())

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

# Trading route
@app.get("/trading", response_class=HTMLResponse)
async def trading(request: Request):
    return templates.TemplateResponse("trading.html", {"request": request})

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

# Stock Search and Quote APIs
@app.get("/api/search-stocks")
async def search_stocks(query: str, exchange: str = None):
    """Search for stocks using Kite Connect"""
    try:
        if not kite_service.kite or not kite_service.access_token:
            raise HTTPException(status_code=400, detail="Kite not connected")

        # Get all instruments
        instruments = kite_service.get_instruments(exchange or "NSE")
        if not instruments:
            return []

        # Filter instruments based on query
        query_upper = query.upper()
        filtered = []

        for instrument in instruments:
            if (query_upper in instrument['tradingsymbol'].upper() or
                query_upper in instrument.get('name', '').upper()):

                # Skip derivatives and other complex instruments for now
                if instrument['instrument_type'] == 'EQ':
                    filtered.append({
                        'symbol': instrument['tradingsymbol'],
                        'name': instrument.get('name', instrument['tradingsymbol']),
                        'exchange': instrument['exchange'],
                        'instrument_token': instrument['instrument_token'],
                        'last_price': None,  # Will be populated by quote API
                        'change': None
                    })

        # Limit results and get quotes for top matches
        top_results = filtered[:10]

        # Get live quotes for the results
        if top_results:
            symbols = [f"{r['exchange']}:{r['symbol']}" for r in top_results]
            quotes = kite_service.get_ltp(symbols)

            if quotes:
                for result in top_results:
                    symbol_key = f"{result['exchange']}:{result['symbol']}"
                    if symbol_key in quotes:
                        quote_data = quotes[symbol_key]
                        result['last_price'] = quote_data.get('last_price')

        return top_results

    except Exception as e:
        logger.error(f"Stock search error: {e}")
        return []

@app.get("/api/stock-quote")
async def get_stock_quote(symbol: str):
    """Get detailed quote for a specific stock"""
    try:
        if not kite_service.kite or not kite_service.access_token:
            raise HTTPException(status_code=400, detail="Kite not connected")

        # Get detailed quote
        quote = kite_service.get_quote([symbol])
        if not quote or symbol not in quote:
            raise HTTPException(status_code=404, detail="Symbol not found")

        data = quote[symbol]

        return {
            'symbol': symbol,
            'last_price': data.get('last_price'),
            'change': data.get('net_change'),
            'change_percent': ((data.get('net_change', 0) / data.get('last_price', 1)) * 100) if data.get('last_price') else 0,
            'high': data.get('ohlc', {}).get('high'),
            'low': data.get('ohlc', {}).get('low'),
            'open': data.get('ohlc', {}).get('open'),
            'close': data.get('ohlc', {}).get('close'),
            'volume': data.get('volume'),
            'average_price': data.get('average_price'),
            'upper_circuit': data.get('upper_circuit_limit'),
            'lower_circuit': data.get('lower_circuit_limit')
        }

    except Exception as e:
        logger.error(f"Quote error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Order Placement API
@app.post("/api/place-order")
async def place_order(order_data: dict, db: Session = Depends(get_db)):
    """Place order through Kite Connect"""
    try:
        if not kite_service.kite or not kite_service.access_token:
            raise HTTPException(status_code=400, detail="Kite not connected")

        # Place the main order
        order_id = kite_service.place_order(
            tradingsymbol=order_data['symbol'],
            exchange=order_data['exchange'],
            transaction_type=order_data['trade_type'],
            quantity=order_data['quantity'],
            order_type=order_data['order_type'],
            price=order_data.get('price'),
            product="CNC"
        )

        if order_id:
            # Save order to database
            trade = Trade(
                user_id=1,  # In production, use current user
                symbol=order_data['symbol'],
                exchange=order_data['exchange'],
                trade_type=order_data['trade_type'],
                order_type=order_data['order_type'],
                quantity=order_data['quantity'],
                price=order_data.get('price', 0),
                total_cost=order_data['quantity'] * order_data.get('price', 0),
                stop_loss=order_data.get('stop_loss'),
                target=order_data.get('target'),
                trade_date=datetime.now(),
                zerodha_order_id=order_id
            )
            db.add(trade)
            db.commit()

            logger.info(f"✅ Order placed: {order_id} for {order_data['symbol']}")
            return {"success": True, "order_id": order_id, "message": "Order placed successfully"}
        else:
            return {"success": False, "message": "Failed to place order"}

    except Exception as e:
        logger.error(f"Order placement error: {e}")
        return {"success": False, "message": str(e)}

# Watchlist API
@app.get("/api/watchlist")
async def get_watchlist(db: Session = Depends(get_db)):
    """Get user's watchlist"""
    try:
        watchlist = db.query(Watchlist).filter(Watchlist.user_id == 1).all()  # In production, use current user

        # Get live quotes for watchlist items
        result = []
        if watchlist and kite_service.kite and kite_service.access_token:
            symbols = [f"{item.exchange}:{item.symbol}" for item in watchlist]
            quotes = kite_service.get_ltp(symbols)

            for item in watchlist:
                symbol_key = f"{item.exchange}:{item.symbol}"
                current_price = None
                change = 0
                change_percent = 0

                if quotes and symbol_key in quotes:
                    quote_data = quotes[symbol_key]
                    current_price = quote_data.get('last_price')

                result.append({
                    'id': item.id,
                    'symbol': item.symbol,
                    'exchange': item.exchange,
                    'name': item.name,
                    'current_price': current_price,
                    'change': change,
                    'change_percent': change_percent,
                    'target_price': item.target_price,
                    'stop_loss_price': item.stop_loss_price,
                    'alert_enabled': item.alert_enabled,
                    'notes': item.notes,
                    'tags': item.tags,
                    'created_at': item.created_at
                })
        else:
            for item in watchlist:
                result.append({
                    'id': item.id,
                    'symbol': item.symbol,
                    'exchange': item.exchange,
                    'name': item.name,
                    'current_price': None,
                    'change': 0,
                    'change_percent': 0,
                    'target_price': item.target_price,
                    'stop_loss_price': item.stop_loss_price,
                    'alert_enabled': item.alert_enabled,
                    'notes': item.notes,
                    'tags': item.tags,
                    'created_at': item.created_at
                })

        return result

    except Exception as e:
        logger.error(f"Get watchlist error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/watchlist")
async def add_to_watchlist(watchlist_data: dict, db: Session = Depends(get_db)):
    """Add stock to watchlist"""
    try:
        # Check if item already exists
        existing = db.query(Watchlist).filter(
            Watchlist.user_id == 1,  # In production, use current user
            Watchlist.symbol == watchlist_data['symbol'],
            Watchlist.exchange == watchlist_data['exchange']
        ).first()

        if existing:
            return {"success": False, "message": "Stock already in watchlist"}

        # Create new watchlist item
        watchlist_item = Watchlist(
            user_id=1,  # In production, use current user
            symbol=watchlist_data['symbol'],
            exchange=watchlist_data['exchange'],
            name=watchlist_data.get('name'),
            target_price=watchlist_data.get('target_price'),
            stop_loss_price=watchlist_data.get('stop_loss_price'),
            alert_enabled=watchlist_data.get('alert_enabled', True),
            notes=watchlist_data.get('notes'),
            tags=watchlist_data.get('tags')
        )

        db.add(watchlist_item)
        db.commit()
        db.refresh(watchlist_item)

        logger.info(f"✅ Added to watchlist: {watchlist_data['symbol']}")
        return {"success": True, "message": "Stock added to watchlist", "id": watchlist_item.id}

    except Exception as e:
        logger.error(f"Add to watchlist error: {e}")
        return {"success": False, "message": str(e)}

@app.put("/api/watchlist/{watchlist_id}")
async def update_watchlist_item(watchlist_id: int, watchlist_data: dict, db: Session = Depends(get_db)):
    """Update watchlist item"""
    try:
        watchlist_item = db.query(Watchlist).filter(
            Watchlist.id == watchlist_id,
            Watchlist.user_id == 1  # In production, use current user
        ).first()

        if not watchlist_item:
            return {"success": False, "message": "Watchlist item not found"}

        # Update fields
        for key, value in watchlist_data.items():
            if hasattr(watchlist_item, key):
                setattr(watchlist_item, key, value)

        db.commit()

        logger.info(f"✅ Updated watchlist item: {watchlist_item.symbol}")
        return {"success": True, "message": "Watchlist item updated"}

    except Exception as e:
        logger.error(f"Update watchlist error: {e}")
        return {"success": False, "message": str(e)}

@app.delete("/api/watchlist/{watchlist_id}")
async def remove_from_watchlist(watchlist_id: int, db: Session = Depends(get_db)):
    """Remove stock from watchlist"""
    try:
        watchlist_item = db.query(Watchlist).filter(
            Watchlist.id == watchlist_id,
            Watchlist.user_id == 1  # In production, use current user
        ).first()

        if not watchlist_item:
            return {"success": False, "message": "Watchlist item not found"}

        symbol = watchlist_item.symbol
        db.delete(watchlist_item)
        db.commit()

        logger.info(f"✅ Removed from watchlist: {symbol}")
        return {"success": True, "message": "Stock removed from watchlist"}

    except Exception as e:
        logger.error(f"Remove from watchlist error: {e}")
        return {"success": False, "message": str(e)}

# WebSocket endpoint for live price feeds
@app.websocket("/ws/prices")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get('action') == 'subscribe':
                symbols = message.get('symbols', [])
                for symbol in symbols:
                    manager.subscribe(websocket, symbol)
                    logger.info(f"Client subscribed to {symbol}")

            elif message.get('action') == 'unsubscribe':
                symbols = message.get('symbols', [])
                for symbol in symbols:
                    manager.unsubscribe(websocket, symbol)
                    logger.info(f"Client unsubscribed from {symbol}")

            elif message.get('action') == 'ping':
                await manager.send_personal_message(json.dumps({'type': 'pong'}), websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# Alert Log API
@app.get("/api/alerts")
async def get_alerts(db: Session = Depends(get_db)):
    """Get user's alert history"""
    try:
        alerts = db.query(AlertLog).filter(AlertLog.user_id == 1).order_by(AlertLog.created_at.desc()).limit(50).all()  # In production, use current user

        result = []
        for alert in alerts:
            result.append({
                'id': alert.id,
                'symbol': alert.symbol,
                'alert_type': alert.alert_type,
                'message': alert.message,
                'current_price': alert.current_price,
                'trigger_price': alert.trigger_price,
                'sent_email': alert.sent_email,
                'sent_sms': alert.sent_sms,
                'created_at': alert.created_at
            })

        return result

    except Exception as e:
        logger.error(f"Get alerts error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# User notification preferences API
@app.get("/api/user/notification-preferences")
async def get_notification_preferences(db: Session = Depends(get_db)):
    """Get user's notification preferences"""
    try:
        user = db.query(User).filter(User.id == 1).first()  # In production, use current user
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            'email': user.email,
            'phone_number': user.phone_number,
            'email_notifications_enabled': user.email_notifications_enabled,
            'sms_notifications_enabled': user.sms_notifications_enabled
        }

    except Exception as e:
        logger.error(f"Get notification preferences error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/user/notification-preferences")
async def update_notification_preferences(preferences: dict, db: Session = Depends(get_db)):
    """Update user's notification preferences"""
    try:
        user = db.query(User).filter(User.id == 1).first()  # In production, use current user
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Update preferences
        if 'phone_number' in preferences:
            user.phone_number = preferences['phone_number']
        if 'email_notifications_enabled' in preferences:
            user.email_notifications_enabled = preferences['email_notifications_enabled']
        if 'sms_notifications_enabled' in preferences:
            user.sms_notifications_enabled = preferences['sms_notifications_enabled']

        db.commit()

        logger.info(f"✅ Updated notification preferences for user {user.username}")
        return {"success": True, "message": "Notification preferences updated"}

    except Exception as e:
        logger.error(f"Update notification preferences error: {e}")
        return {"success": False, "message": str(e)}

# Test notification endpoint
@app.post("/api/test-notification")
async def test_notification(test_data: dict, db: Session = Depends(get_db)):
    """Test notification system"""
    try:
        user_id = 1  # In production, use current user
        alert_type = test_data.get('alert_type', 'TARGET_REACHED')
        symbol = test_data.get('symbol', 'RELIANCE')

        # Create a test message
        message = f"{symbol} target price ₹2500 reached! Current: ₹2550"

        # Send test notification
        await send_alert_notification(user_id, message, alert_type)

        return {"success": True, "message": "Test notification sent"}

    except Exception as e:
        logger.error(f"Test notification error: {e}")
        return {"success": False, "message": str(e)}

# Executable Watchlist Features
@app.post("/api/watchlist/{watchlist_id}/quick-buy")
async def quick_buy_from_watchlist(watchlist_id: int, order_data: dict, db: Session = Depends(get_db)):
    """Execute quick buy order from watchlist item"""
    try:
        # Get watchlist item
        watchlist_item = db.query(Watchlist).filter(
            Watchlist.id == watchlist_id,
            Watchlist.user_id == 1  # In production, use current user
        ).first()

        if not watchlist_item:
            return {"success": False, "message": "Watchlist item not found"}

        if not kite_service.kite or not kite_service.access_token:
            return {"success": False, "message": "Kite not connected"}

        # Get current price
        symbol_key = f"{watchlist_item.exchange}:{watchlist_item.symbol}"
        quotes = kite_service.get_ltp([symbol_key])

        if not quotes or symbol_key not in quotes:
            return {"success": False, "message": "Unable to get current price"}

        current_price = quotes[symbol_key].get('last_price')

        # Prepare order data
        quantity = order_data.get('quantity', 1)
        order_type = order_data.get('order_type', 'MARKET')
        price = order_data.get('price', current_price)

        # Place buy order
        order_id = kite_service.place_order(
            tradingsymbol=watchlist_item.symbol,
            exchange=watchlist_item.exchange,
            transaction_type="BUY",
            quantity=quantity,
            order_type=order_type,
            price=price,
            product="CNC"
        )

        if order_id:
            # Save trade to database
            trade = Trade(
                user_id=1,  # In production, use current user
                symbol=watchlist_item.symbol,
                exchange=watchlist_item.exchange,
                trade_type="BUY",
                order_type=order_type,
                quantity=quantity,
                price=price,
                total_cost=quantity * price,
                trade_date=datetime.now(),
                zerodha_order_id=order_id
            )
            db.add(trade)
            db.commit()

            logger.info(f"✅ Quick buy order placed from watchlist: {order_id} for {watchlist_item.symbol}")
            return {
                "success": True,
                "order_id": order_id,
                "message": f"Buy order placed for {quantity} shares of {watchlist_item.symbol}",
                "current_price": current_price
            }
        else:
            return {"success": False, "message": "Failed to place order"}

    except Exception as e:
        logger.error(f"Quick buy error: {e}")
        return {"success": False, "message": str(e)}

@app.post("/api/watchlist/{watchlist_id}/quick-sell")
async def quick_sell_from_watchlist(watchlist_id: int, order_data: dict, db: Session = Depends(get_db)):
    """Execute quick sell order from watchlist item"""
    try:
        # Get watchlist item
        watchlist_item = db.query(Watchlist).filter(
            Watchlist.id == watchlist_id,
            Watchlist.user_id == 1  # In production, use current user
        ).first()

        if not watchlist_item:
            return {"success": False, "message": "Watchlist item not found"}

        if not kite_service.kite or not kite_service.access_token:
            return {"success": False, "message": "Kite not connected"}

        # Check if user has holdings for this symbol
        holding = db.query(Holding).filter(
            Holding.user_id == 1,  # In production, use current user
            Holding.symbol == watchlist_item.symbol,
            Holding.exchange == watchlist_item.exchange
        ).first()

        if not holding or holding.quantity <= 0:
            return {"success": False, "message": "No holdings found for this symbol"}

        # Get current price
        symbol_key = f"{watchlist_item.exchange}:{watchlist_item.symbol}"
        quotes = kite_service.get_ltp([symbol_key])

        if not quotes or symbol_key not in quotes:
            return {"success": False, "message": "Unable to get current price"}

        current_price = quotes[symbol_key].get('last_price')

        # Prepare order data
        quantity = min(order_data.get('quantity', holding.quantity), holding.quantity)
        order_type = order_data.get('order_type', 'MARKET')
        price = order_data.get('price', current_price)

        # Place sell order
        order_id = kite_service.place_order(
            tradingsymbol=watchlist_item.symbol,
            exchange=watchlist_item.exchange,
            transaction_type="SELL",
            quantity=quantity,
            order_type=order_type,
            price=price,
            product="CNC"
        )

        if order_id:
            # Save trade to database
            trade = Trade(
                user_id=1,  # In production, use current user
                symbol=watchlist_item.symbol,
                exchange=watchlist_item.exchange,
                trade_type="SELL",
                order_type=order_type,
                quantity=quantity,
                price=price,
                total_cost=quantity * price,
                trade_date=datetime.now(),
                zerodha_order_id=order_id
            )
            db.add(trade)
            db.commit()

            logger.info(f"✅ Quick sell order placed from watchlist: {order_id} for {watchlist_item.symbol}")
            return {
                "success": True,
                "order_id": order_id,
                "message": f"Sell order placed for {quantity} shares of {watchlist_item.symbol}",
                "current_price": current_price
            }
        else:
            return {"success": False, "message": "Failed to place order"}

    except Exception as e:
        logger.error(f"Quick sell error: {e}")
        return {"success": False, "message": str(e)}

@app.post("/api/watchlist/{watchlist_id}/set-alerts")
async def set_watchlist_alerts(watchlist_id: int, alert_data: dict, db: Session = Depends(get_db)):
    """Set price alerts for watchlist item"""
    try:
        # Get watchlist item
        watchlist_item = db.query(Watchlist).filter(
            Watchlist.id == watchlist_id,
            Watchlist.user_id == 1  # In production, use current user
        ).first()

        if not watchlist_item:
            return {"success": False, "message": "Watchlist item not found"}

        # Update alert settings
        if 'target_price' in alert_data:
            watchlist_item.target_price = alert_data['target_price']
        if 'stop_loss_price' in alert_data:
            watchlist_item.stop_loss_price = alert_data['stop_loss_price']
        if 'alert_enabled' in alert_data:
            watchlist_item.alert_enabled = alert_data['alert_enabled']

        db.commit()

        logger.info(f"✅ Alert settings updated for {watchlist_item.symbol}")
        return {
            "success": True,
            "message": f"Alert settings updated for {watchlist_item.symbol}",
            "target_price": watchlist_item.target_price,
            "stop_loss_price": watchlist_item.stop_loss_price,
            "alert_enabled": watchlist_item.alert_enabled
        }

    except Exception as e:
        logger.error(f"Set alerts error: {e}")
        return {"success": False, "message": str(e)}

@app.get("/api/watchlist/{watchlist_id}/order-suggestions")
async def get_order_suggestions(watchlist_id: int, db: Session = Depends(get_db)):
    """Get intelligent order suggestions for watchlist item"""
    try:
        # Get watchlist item
        watchlist_item = db.query(Watchlist).filter(
            Watchlist.id == watchlist_id,
            Watchlist.user_id == 1  # In production, use current user
        ).first()

        if not watchlist_item:
            return {"success": False, "message": "Watchlist item not found"}

        if not kite_service.kite or not kite_service.access_token:
            return {"success": False, "message": "Kite not connected"}

        # Get current quote
        symbol_key = f"{watchlist_item.exchange}:{watchlist_item.symbol}"
        quotes = kite_service.get_quote([symbol_key])

        if not quotes or symbol_key not in quotes:
            return {"success": False, "message": "Unable to get quote data"}

        quote_data = quotes[symbol_key]
        current_price = quote_data.get('last_price', 0)
        ohlc = quote_data.get('ohlc', {})

        # Check holdings
        holding = db.query(Holding).filter(
            Holding.user_id == 1,  # In production, use current user
            Holding.symbol == watchlist_item.symbol,
            Holding.exchange == watchlist_item.exchange
        ).first()

        # Generate suggestions based on technical levels and holdings
        suggestions = {
            'symbol': watchlist_item.symbol,
            'current_price': current_price,
            'has_holding': bool(holding and holding.quantity > 0),
            'holding_quantity': holding.quantity if holding else 0,
            'holding_avg_price': holding.average_price if holding else 0,
            'day_high': ohlc.get('high'),
            'day_low': ohlc.get('low'),
            'day_open': ohlc.get('open'),
            'suggestions': []
        }

        # Buy suggestions
        if current_price < ohlc.get('high', current_price) * 0.98:  # Near day high
            suggestions['suggestions'].append({
                'action': 'BUY',
                'reason': 'Price near day high - momentum trade',
                'suggested_price': current_price,
                'suggested_quantity': 10,
                'stop_loss': current_price * 0.95,
                'target': current_price * 1.05
            })

        if current_price < ohlc.get('low', current_price) * 1.02:  # Near day low
            suggestions['suggestions'].append({
                'action': 'BUY',
                'reason': 'Price near day low - value opportunity',
                'suggested_price': current_price,
                'suggested_quantity': 20,
                'stop_loss': ohlc.get('low', current_price) * 0.98,
                'target': current_price * 1.03
            })

        # Sell suggestions (if holding)
        if holding and holding.quantity > 0:
            unrealized_pnl_pct = ((current_price - holding.average_price) / holding.average_price) * 100

            if unrealized_pnl_pct > 5:  # Profit booking
                suggestions['suggestions'].append({
                    'action': 'SELL',
                    'reason': f'Book profits - {unrealized_pnl_pct:.1f}% gain',
                    'suggested_price': current_price,
                    'suggested_quantity': holding.quantity // 2,  # Partial booking
                    'current_pnl': unrealized_pnl_pct
                })

            if unrealized_pnl_pct < -5:  # Stop loss
                suggestions['suggestions'].append({
                    'action': 'SELL',
                    'reason': f'Stop loss - {abs(unrealized_pnl_pct):.1f}% loss',
                    'suggested_price': current_price,
                    'suggested_quantity': holding.quantity,
                    'current_pnl': unrealized_pnl_pct
                })

        return suggestions

    except Exception as e:
        logger.error(f"Order suggestions error: {e}")
        return {"success": False, "message": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)