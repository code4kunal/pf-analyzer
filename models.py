from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Text, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum
from datetime import datetime

class TradeType(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(str, enum.Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    SL = "SL"
    SL_M = "SL_M"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Contact preferences
    phone_number = Column(String, nullable=True)
    email_notifications_enabled = Column(Boolean, default=True)
    sms_notifications_enabled = Column(Boolean, default=False)

    # Zerodha credentials (encrypted in production)
    kite_user_id = Column(String, nullable=True)
    kite_access_token = Column(Text, nullable=True)
    kite_refresh_token = Column(Text, nullable=True)

    # Relationships
    trades = relationship("Trade", back_populates="user", cascade="all, delete-orphan")
    journal_entries = relationship("JournalEntry", back_populates="user", cascade="all, delete-orphan")
    holdings = relationship("Holding", back_populates="user", cascade="all, delete-orphan")
    watchlist_items = relationship("Watchlist", back_populates="user", cascade="all, delete-orphan")
    alert_logs = relationship("AlertLog", back_populates="user", cascade="all, delete-orphan")

class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Trade details
    symbol = Column(String, nullable=False, index=True)
    exchange = Column(String, nullable=False)
    trade_type = Column(Enum(TradeType), nullable=False)
    order_type = Column(Enum(OrderType), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)

    # Financial details
    brokerage = Column(Float, default=0)
    taxes = Column(Float, default=0)
    total_cost = Column(Float, nullable=False)

    # Trade management
    stop_loss = Column(Float, nullable=True)
    target = Column(Float, nullable=True)
    actual_exit_price = Column(Float, nullable=True)

    # Timestamps
    trade_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # External references
    zerodha_order_id = Column(String, nullable=True)
    zerodha_trade_id = Column(String, nullable=True)

    # Relationships
    user = relationship("User", back_populates="trades")
    journal_entry = relationship("JournalEntry", back_populates="trade", uselist=False, cascade="all, delete-orphan")

class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    trade_id = Column(Integer, ForeignKey("trades.id"), nullable=True)

    # Journal content
    entry_date = Column(Date, nullable=False, index=True)
    title = Column(String, nullable=False)
    strategy = Column(String, nullable=True)

    # Analysis
    entry_reason = Column(Text, nullable=True)
    exit_reason = Column(Text, nullable=True)
    market_condition = Column(Text, nullable=True)

    # Reflection
    mistakes = Column(Text, nullable=True)
    learnings = Column(Text, nullable=True)
    emotions = Column(String, nullable=True)

    # Performance
    rating = Column(Integer, nullable=True)  # 1-5 rating
    followed_rules = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="journal_entries")
    trade = relationship("Trade", back_populates="journal_entry")

class Holding(Base):
    __tablename__ = "holdings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Holding details
    symbol = Column(String, nullable=False, index=True)
    exchange = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    average_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=True)

    # P&L
    unrealized_pnl = Column(Float, nullable=True)
    unrealized_pnl_percentage = Column(Float, nullable=True)

    # Timestamps
    last_updated = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="holdings")

class PerformanceSnapshot(Base):
    __tablename__ = "performance_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Snapshot date
    snapshot_date = Column(Date, nullable=False, index=True)

    # Portfolio value
    total_investment = Column(Float, nullable=False)
    current_value = Column(Float, nullable=False)

    # Returns
    absolute_returns = Column(Float, nullable=False)
    percentage_returns = Column(Float, nullable=False)

    # Advanced metrics
    xirr = Column(Float, nullable=True)
    cagr = Column(Float, nullable=True)

    # Risk metrics
    max_drawdown = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    win_rate = Column(Float, nullable=True)

    # Trade statistics
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Watchlist(Base):
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Stock details
    symbol = Column(String, nullable=False, index=True)
    exchange = Column(String, nullable=False)
    name = Column(String, nullable=True)

    # Alert settings
    target_price = Column(Float, nullable=True)
    stop_loss_price = Column(Float, nullable=True)
    alert_enabled = Column(Boolean, default=True)

    # Notes and tags
    notes = Column(Text, nullable=True)
    tags = Column(String, nullable=True)  # Comma-separated tags

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="watchlist_items")

class AlertLog(Base):
    __tablename__ = "alert_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    watchlist_id = Column(Integer, ForeignKey("watchlist.id"), nullable=True)

    # Alert details
    symbol = Column(String, nullable=False)
    alert_type = Column(String, nullable=False)  # 'PRICE_TARGET', 'STOP_LOSS', 'VOLUME', etc.
    message = Column(Text, nullable=False)
    current_price = Column(Float, nullable=True)
    trigger_price = Column(Float, nullable=True)

    # Delivery status
    sent_email = Column(Boolean, default=False)
    sent_sms = Column(Boolean, default=False)
    sent_push = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="alert_logs")
    watchlist_item = relationship("Watchlist")