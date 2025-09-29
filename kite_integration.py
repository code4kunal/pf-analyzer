from kiteconnect import KiteConnect
from config import settings
from typing import Optional, Dict, List
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class KiteService:
    def __init__(self):
        self.kite = None
        self.api_key = settings.kite_api_key
        self.api_secret = settings.kite_api_secret
        self.access_token = settings.kite_access_token

    def initialize(self, access_token: str = None):
        """Initialize Kite Connect with access token"""
        try:
            self.kite = KiteConnect(api_key=self.api_key)
            if access_token:
                self.access_token = access_token
            if self.access_token:
                self.kite.set_access_token(self.access_token)
                return True
            return False
        except Exception as e:
            logger.error(f"Error initializing Kite: {e}")
            return False

    def get_login_url(self) -> str:
        """Get Kite login URL for user authentication"""
        if not self.kite:
            self.kite = KiteConnect(api_key=self.api_key)
        return self.kite.login_url()

    def generate_session(self, request_token: str) -> Optional[Dict]:
        """Generate access token from request token"""
        try:
            if not self.kite:
                self.kite = KiteConnect(api_key=self.api_key)

            data = self.kite.generate_session(request_token, api_secret=self.api_secret)
            self.access_token = data["access_token"]
            self.kite.set_access_token(self.access_token)
            return data
        except Exception as e:
            logger.error(f"Error generating session: {e}")
            return None

    def get_profile(self) -> Optional[Dict]:
        """Get user profile"""
        try:
            if not self.kite or not self.access_token:
                return None
            return self.kite.profile()
        except Exception as e:
            logger.error(f"Error fetching profile: {e}")
            return None

    def get_positions(self) -> Optional[Dict]:
        """Get current positions"""
        try:
            if not self.kite or not self.access_token:
                return None
            return self.kite.positions()
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return None

    def get_holdings(self) -> Optional[List[Dict]]:
        """Get current holdings"""
        try:
            if not self.kite or not self.access_token:
                return None
            return self.kite.holdings()
        except Exception as e:
            logger.error(f"Error fetching holdings: {e}")
            return None

    def get_orders(self) -> Optional[List[Dict]]:
        """Get all orders for the day"""
        try:
            if not self.kite or not self.access_token:
                return None
            return self.kite.orders()
        except Exception as e:
            logger.error(f"Error fetching orders: {e}")
            return None

    def get_trades(self) -> Optional[List[Dict]]:
        """Get all executed trades for the day"""
        try:
            if not self.kite or not self.access_token:
                return None
            return self.kite.trades()
        except Exception as e:
            logger.error(f"Error fetching trades: {e}")
            return None

    def get_historical_data(self, instrument_token: str, from_date: datetime, to_date: datetime, interval: str = "day") -> Optional[List[Dict]]:
        """Get historical data for an instrument"""
        try:
            if not self.kite or not self.access_token:
                return None
            return self.kite.historical_data(
                instrument_token=instrument_token,
                from_date=from_date,
                to_date=to_date,
                interval=interval
            )
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            return None

    def place_order(self, tradingsymbol: str, exchange: str, transaction_type: str,
                    quantity: int, order_type: str = "MARKET", price: float = None,
                    trigger_price: float = None, product: str = "CNC") -> Optional[str]:
        """Place an order"""
        try:
            if not self.kite or not self.access_token:
                return None

            order_params = {
                "tradingsymbol": tradingsymbol,
                "exchange": exchange,
                "transaction_type": transaction_type,
                "quantity": quantity,
                "order_type": order_type,
                "product": product,
                "variety": "regular"
            }

            if order_type == "LIMIT" and price:
                order_params["price"] = price

            if trigger_price:
                order_params["trigger_price"] = trigger_price

            order_id = self.kite.place_order(**order_params)
            return order_id
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return None

    def get_instruments(self, exchange: str = "NSE") -> Optional[List[Dict]]:
        """Get all instruments for an exchange"""
        try:
            if not self.kite:
                self.kite = KiteConnect(api_key=self.api_key)
            return self.kite.instruments(exchange)
        except Exception as e:
            logger.error(f"Error fetching instruments: {e}")
            return None

    def get_quote(self, instruments: List[str]) -> Optional[Dict]:
        """Get live quotes for instruments"""
        try:
            if not self.kite or not self.access_token:
                return None
            return self.kite.quote(instruments)
        except Exception as e:
            logger.error(f"Error fetching quotes: {e}")
            return None

    def get_ltp(self, instruments: List[str]) -> Optional[Dict]:
        """Get last traded price for instruments"""
        try:
            if not self.kite or not self.access_token:
                return None
            return self.kite.ltp(instruments)
        except Exception as e:
            logger.error(f"Error fetching LTP: {e}")
            return None

# Singleton instance
kite_service = KiteService()