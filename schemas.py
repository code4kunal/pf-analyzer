from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List
from models import TradeType, OrderType

# User schemas
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Trade schemas
class TradeCreate(BaseModel):
    symbol: str
    exchange: str
    trade_type: TradeType
    order_type: OrderType
    quantity: int
    price: float
    brokerage: Optional[float] = 0
    taxes: Optional[float] = 0
    stop_loss: Optional[float] = None
    target: Optional[float] = None
    trade_date: datetime
    zerodha_order_id: Optional[str] = None

class TradeUpdate(BaseModel):
    actual_exit_price: Optional[float] = None
    stop_loss: Optional[float] = None
    target: Optional[float] = None

class TradeResponse(BaseModel):
    id: int
    symbol: str
    exchange: str
    trade_type: TradeType
    order_type: OrderType
    quantity: int
    price: float
    total_cost: float
    stop_loss: Optional[float]
    target: Optional[float]
    actual_exit_price: Optional[float]
    trade_date: datetime
    created_at: datetime

    class Config:
        from_attributes = True

# Journal schemas
class JournalCreate(BaseModel):
    trade_id: Optional[int] = None
    entry_date: date
    title: str
    strategy: Optional[str] = None
    entry_reason: Optional[str] = None
    exit_reason: Optional[str] = None
    market_condition: Optional[str] = None
    mistakes: Optional[str] = None
    learnings: Optional[str] = None
    emotions: Optional[str] = None
    rating: Optional[int] = None
    followed_rules: Optional[bool] = True

class JournalUpdate(BaseModel):
    title: Optional[str] = None
    strategy: Optional[str] = None
    entry_reason: Optional[str] = None
    exit_reason: Optional[str] = None
    market_condition: Optional[str] = None
    mistakes: Optional[str] = None
    learnings: Optional[str] = None
    emotions: Optional[str] = None
    rating: Optional[int] = None
    followed_rules: Optional[bool] = None

class JournalResponse(BaseModel):
    id: int
    trade_id: Optional[int]
    entry_date: date
    title: str
    strategy: Optional[str]
    entry_reason: Optional[str]
    exit_reason: Optional[str]
    market_condition: Optional[str]
    mistakes: Optional[str]
    learnings: Optional[str]
    emotions: Optional[str]
    rating: Optional[int]
    followed_rules: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Holding schemas
class HoldingResponse(BaseModel):
    id: int
    symbol: str
    exchange: str
    quantity: int
    average_price: float
    current_price: Optional[float]
    unrealized_pnl: Optional[float]
    unrealized_pnl_percentage: Optional[float]
    last_updated: datetime

    class Config:
        from_attributes = True

# Performance schemas
class PerformanceMetrics(BaseModel):
    total_investment: float
    current_value: float
    absolute_returns: float
    percentage_returns: float
    xirr: Optional[float]
    cagr: Optional[float]
    max_drawdown: Optional[float]
    sharpe_ratio: Optional[float]
    win_rate: Optional[float]
    total_trades: int
    winning_trades: int
    losing_trades: int

class PerformanceFilter(BaseModel):
    period: str  # "1M", "3M", "6M", "1Y", "ALL"

# Kite auth schemas
class KiteAuthRequest(BaseModel):
    request_token: str

class KiteAuthResponse(BaseModel):
    success: bool
    message: str
    user_id: Optional[str] = None