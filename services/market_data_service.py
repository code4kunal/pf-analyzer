"""
Market Data Service - NSE/BSE Integration
Handles real-time stock prices, mutual fund NAV, and market data
"""

import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class MarketDataService:
    """
    Service for fetching market data from NSE/BSE and mutual fund APIs

    Note: This implementation uses free/public APIs. For production, consider:
    - NSE Official API (requires registration)
    - Yahoo Finance API
    - Alpha Vantage API
    - RapidAPI market data services
    """

    # API Endpoints
    YAHOO_FINANCE_BASE = "https://query1.finance.yahoo.com/v8/finance"
    NSE_BASE_URL = "https://www.nseindia.com/api"

    # Headers to mimic browser request (NSE blocks basic requests)
    NSE_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    @staticmethod
    def get_stock_quote(symbol: str, exchange: str = "NSE") -> Optional[Dict]:
        """
        Get real-time stock quote from NSE/BSE

        Args:
            symbol: Stock symbol (e.g., "RELIANCE", "TCS")
            exchange: Exchange name - "NSE" or "BSE"

        Returns:
            Dictionary with stock data or None if failed
        """
        try:
            # Format symbol for Yahoo Finance
            if exchange == "NSE":
                yahoo_symbol = f"{symbol}.NS"
            elif exchange == "BSE":
                yahoo_symbol = f"{symbol}.BO"
            else:
                yahoo_symbol = symbol

            # Fetch from Yahoo Finance (free and reliable)
            url = f"{MarketDataService.YAHOO_FINANCE_BASE}/quote"
            params = {
                'symbols': yahoo_symbol,
                'fields': 'regularMarketPrice,regularMarketChange,regularMarketChangePercent,regularMarketDayHigh,regularMarketDayLow,regularMarketVolume,fiftyTwoWeekHigh,fiftyTwoWeekLow,marketCap,trailingPE,dividendYield'
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if 'quoteResponse' in data and 'result' in data['quoteResponse']:
                quotes = data['quoteResponse']['result']
                if quotes:
                    quote = quotes[0]
                    return {
                        'symbol': symbol,
                        'exchange': exchange,
                        'price': quote.get('regularMarketPrice'),
                        'change': quote.get('regularMarketChange'),
                        'change_percent': quote.get('regularMarketChangePercent'),
                        'day_high': quote.get('regularMarketDayHigh'),
                        'day_low': quote.get('regularMarketDayLow'),
                        'volume': quote.get('regularMarketVolume'),
                        '52_week_high': quote.get('fiftyTwoWeekHigh'),
                        '52_week_low': quote.get('fiftyTwoWeekLow'),
                        'market_cap': quote.get('marketCap'),
                        'pe_ratio': quote.get('trailingPE'),
                        'dividend_yield': quote.get('dividendYield'),
                        'last_updated': datetime.now().isoformat()
                    }

            return None

        except Exception as e:
            logger.error(f"Error fetching stock quote for {symbol}: {str(e)}")
            return None

    @staticmethod
    def get_stock_historical_data(
        symbol: str,
        exchange: str = "NSE",
        period: str = "1y"  # 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    ) -> Optional[Dict]:
        """
        Get historical stock data for returns calculation

        Args:
            symbol: Stock symbol
            exchange: Exchange name
            period: Time period for historical data

        Returns:
            Dictionary with historical data
        """
        try:
            # Format symbol for Yahoo Finance
            if exchange == "NSE":
                yahoo_symbol = f"{symbol}.NS"
            elif exchange == "BSE":
                yahoo_symbol = f"{symbol}.BO"
            else:
                yahoo_symbol = symbol

            url = f"{MarketDataService.YAHOO_FINANCE_BASE}/chart/{yahoo_symbol}"
            params = {
                'range': period,
                'interval': '1d'
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if 'chart' in data and 'result' in data['chart']:
                result = data['chart']['result'][0]
                timestamps = result.get('timestamp', [])
                quotes = result.get('indicators', {}).get('quote', [{}])[0]

                return {
                    'symbol': symbol,
                    'exchange': exchange,
                    'timestamps': timestamps,
                    'close_prices': quotes.get('close', []),
                    'high_prices': quotes.get('high', []),
                    'low_prices': quotes.get('low', []),
                    'volumes': quotes.get('volume', [])
                }

            return None

        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
            return None

    @staticmethod
    def calculate_returns(historical_data: Dict) -> Dict[str, float]:
        """
        Calculate various return metrics from historical data

        Args:
            historical_data: Historical price data

        Returns:
            Dictionary with return percentages
        """
        try:
            close_prices = historical_data.get('close_prices', [])
            if not close_prices or len(close_prices) < 2:
                return {}

            # Remove None values
            valid_prices = [p for p in close_prices if p is not None]
            if len(valid_prices) < 2:
                return {}

            current_price = valid_prices[-1]

            returns = {}

            # Calculate returns for different periods
            # Approximate based on available data points
            total_days = len(valid_prices)

            if total_days >= 252:  # ~1 year
                year_ago_price = valid_prices[-252] if len(valid_prices) >= 252 else valid_prices[0]
                returns['return_1y'] = ((current_price - year_ago_price) / year_ago_price) * 100

            if total_days >= 756:  # ~3 years
                three_years_ago = valid_prices[-756] if len(valid_prices) >= 756 else valid_prices[0]
                returns['return_3y'] = ((current_price - three_years_ago) / three_years_ago) * 100

            if total_days >= 1260:  # ~5 years
                five_years_ago = valid_prices[-1260] if len(valid_prices) >= 1260 else valid_prices[0]
                returns['return_5y'] = ((current_price - five_years_ago) / five_years_ago) * 100

            # 1 month return
            if total_days >= 21:
                month_ago = valid_prices[-21]
                returns['return_1m'] = ((current_price - month_ago) / month_ago) * 100

            # 3 month return
            if total_days >= 63:
                three_months_ago = valid_prices[-63]
                returns['return_3m'] = ((current_price - three_months_ago) / three_months_ago) * 100

            # 6 month return
            if total_days >= 126:
                six_months_ago = valid_prices[-126]
                returns['return_6m'] = ((current_price - six_months_ago) / six_months_ago) * 100

            return returns

        except Exception as e:
            logger.error(f"Error calculating returns: {str(e)}")
            return {}

    @staticmethod
    def get_mutual_fund_nav(scheme_code: str) -> Optional[Dict]:
        """
        Get mutual fund NAV from AMFI/MFI API

        Args:
            scheme_code: Mutual fund scheme code

        Returns:
            Dictionary with NAV data
        """
        try:
            # Using MFI API (free)
            url = f"https://api.mfapi.in/mf/{scheme_code}"

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data and 'data' in data:
                latest_nav = data['data'][0] if data['data'] else None

                if latest_nav:
                    return {
                        'scheme_code': scheme_code,
                        'scheme_name': data.get('meta', {}).get('scheme_name'),
                        'fund_house': data.get('meta', {}).get('fund_house'),
                        'scheme_type': data.get('meta', {}).get('scheme_type'),
                        'scheme_category': data.get('meta', {}).get('scheme_category'),
                        'nav': float(latest_nav.get('nav')),
                        'date': latest_nav.get('date'),
                        'last_updated': datetime.now().isoformat()
                    }

            return None

        except Exception as e:
            logger.error(f"Error fetching NAV for scheme {scheme_code}: {str(e)}")
            return None

    @staticmethod
    def search_mutual_funds(query: str) -> List[Dict]:
        """
        Search for mutual funds by name

        Args:
            query: Search query (fund name, AMC name, etc.)

        Returns:
            List of matching funds
        """
        try:
            # Using MFI API search (limited functionality)
            # For production, consider using paid APIs or maintaining local database

            # Note: MFI API doesn't have direct search, so this is a placeholder
            # In production, you would:
            # 1. Maintain a local database of all mutual funds
            # 2. Use ElasticSearch for fast searching
            # 3. Or use paid APIs like RapidAPI MF search

            logger.warning("Mutual fund search not fully implemented. Use scheme code for now.")
            return []

        except Exception as e:
            logger.error(f"Error searching mutual funds: {str(e)}")
            return []

    @staticmethod
    def get_nifty_index_quote(index_name: str = "NIFTY 50") -> Optional[Dict]:
        """
        Get Nifty index quote

        Args:
            index_name: Index name (e.g., "NIFTY 50", "NIFTY BANK")

        Returns:
            Dictionary with index data
        """
        try:
            # Map index names to Yahoo Finance symbols
            index_map = {
                "NIFTY 50": "^NSEI",
                "SENSEX": "^BSESN",
                "NIFTY BANK": "^NSEBANK",
                "NIFTY IT": "^CNXIT",
                "NIFTY MIDCAP 100": "NIFTYMIDCAP100.NS",
                "NIFTY SMALLCAP 100": "NIFTYSMALLCAP100.NS"
            }

            yahoo_symbol = index_map.get(index_name)
            if not yahoo_symbol:
                return None

            url = f"{MarketDataService.YAHOO_FINANCE_BASE}/quote"
            params = {
                'symbols': yahoo_symbol,
                'fields': 'regularMarketPrice,regularMarketChange,regularMarketChangePercent'
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if 'quoteResponse' in data and 'result' in data['quoteResponse']:
                quotes = data['quoteResponse']['result']
                if quotes:
                    quote = quotes[0]
                    return {
                        'index_name': index_name,
                        'value': quote.get('regularMarketPrice'),
                        'change': quote.get('regularMarketChange'),
                        'change_percent': quote.get('regularMarketChangePercent'),
                        'last_updated': datetime.now().isoformat()
                    }

            return None

        except Exception as e:
            logger.error(f"Error fetching index quote for {index_name}: {str(e)}")
            return None

    @staticmethod
    def bulk_update_stock_prices(symbols: List[tuple]) -> Dict[str, Dict]:
        """
        Update prices for multiple stocks in one call

        Args:
            symbols: List of tuples [(symbol, exchange), ...]

        Returns:
            Dictionary mapping symbol to quote data
        """
        results = {}

        for symbol, exchange in symbols:
            quote = MarketDataService.get_stock_quote(symbol, exchange)
            if quote:
                results[symbol] = quote

        return results

    @staticmethod
    def get_stock_fundamentals(symbol: str, exchange: str = "NSE") -> Optional[Dict]:
        """
        Get fundamental data for a stock

        Args:
            symbol: Stock symbol
            exchange: Exchange name

        Returns:
            Dictionary with fundamental metrics
        """
        try:
            # Format symbol for Yahoo Finance
            if exchange == "NSE":
                yahoo_symbol = f"{symbol}.NS"
            elif exchange == "BSE":
                yahoo_symbol = f"{symbol}.BO"
            else:
                yahoo_symbol = symbol

            # Get quote summary (includes fundamentals)
            url = f"{MarketDataService.YAHOO_FINANCE_BASE}/quoteSummary/{yahoo_symbol}"
            params = {
                'modules': 'defaultKeyStatistics,financialData,summaryDetail'
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if 'quoteSummary' in data and 'result' in data['quoteSummary']:
                result = data['quoteSummary']['result'][0]

                stats = result.get('defaultKeyStatistics', {})
                financial = result.get('financialData', {})
                summary = result.get('summaryDetail', {})

                return {
                    'symbol': symbol,
                    'exchange': exchange,
                    'pe_ratio': stats.get('trailingPE', {}).get('raw'),
                    'pb_ratio': stats.get('priceToBook', {}).get('raw'),
                    'dividend_yield': summary.get('dividendYield', {}).get('raw'),
                    'market_cap': summary.get('marketCap', {}).get('raw'),
                    'beta': stats.get('beta', {}).get('raw'),
                    'eps': stats.get('trailingEps', {}).get('raw'),
                    'revenue_growth': financial.get('revenueGrowth', {}).get('raw'),
                    'profit_margin': financial.get('profitMargins', {}).get('raw'),
                    'roe': financial.get('returnOnEquity', {}).get('raw'),
                    'debt_to_equity': financial.get('debtToEquity', {}).get('raw'),
                    'last_updated': datetime.now().isoformat()
                }

            return None

        except Exception as e:
            logger.error(f"Error fetching fundamentals for {symbol}: {str(e)}")
            return None

    @staticmethod
    def is_market_open() -> bool:
        """
        Check if Indian stock market is currently open

        Returns:
            True if market is open, False otherwise
        """
        now = datetime.now()

        # Check if it's a weekday (Monday = 0, Sunday = 6)
        if now.weekday() >= 5:  # Saturday or Sunday
            return False

        # Market hours: 9:15 AM to 3:30 PM IST
        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)

        return market_open <= now <= market_close
