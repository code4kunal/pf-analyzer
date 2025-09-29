import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
import models
from pyxirr import xirr, xnpv

class PerformanceCalculator:
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    def calculate_xirr(self, cashflows: List[Tuple[date, float]]) -> Optional[float]:
        """Calculate XIRR for given cashflows"""
        try:
            if not cashflows or len(cashflows) < 2:
                return None

            # Convert to format required by pyxirr
            dates = [cf[0] for cf in cashflows]
            amounts = [cf[1] for cf in cashflows]

            result = xirr(dates, amounts)
            return round(result * 100, 2) if result is not None else None
        except Exception as e:
            print(f"Error calculating XIRR: {e}")
            return None

    def calculate_cagr(self, initial_value: float, final_value: float, years: float) -> Optional[float]:
        """Calculate CAGR"""
        try:
            if initial_value <= 0 or years <= 0:
                return None

            cagr = ((final_value / initial_value) ** (1/years) - 1) * 100
            return round(cagr, 2)
        except Exception as e:
            print(f"Error calculating CAGR: {e}")
            return None

    def calculate_max_drawdown(self, values: List[float]) -> Optional[float]:
        """Calculate maximum drawdown"""
        try:
            if not values:
                return None

            peak = values[0]
            max_dd = 0

            for value in values:
                if value > peak:
                    peak = value
                dd = ((peak - value) / peak) * 100
                if dd > max_dd:
                    max_dd = dd

            return round(max_dd, 2)
        except Exception as e:
            print(f"Error calculating max drawdown: {e}")
            return None

    def calculate_sharpe_ratio(self, returns: List[float], risk_free_rate: float = 0.05) -> Optional[float]:
        """Calculate Sharpe ratio"""
        try:
            if not returns or len(returns) < 2:
                return None

            returns_array = np.array(returns)
            excess_returns = returns_array - risk_free_rate/252  # Daily risk-free rate

            mean_excess_return = np.mean(excess_returns)
            std_excess_return = np.std(excess_returns)

            if std_excess_return == 0:
                return None

            sharpe = mean_excess_return / std_excess_return * np.sqrt(252)  # Annualized
            return round(sharpe, 2)
        except Exception as e:
            print(f"Error calculating Sharpe ratio: {e}")
            return None

    def get_trades_for_period(self, period: str) -> List[models.Trade]:
        """Get trades for specified period"""
        end_date = datetime.now()

        if period == "1M":
            start_date = end_date - timedelta(days=30)
        elif period == "3M":
            start_date = end_date - timedelta(days=90)
        elif period == "6M":
            start_date = end_date - timedelta(days=180)
        elif period == "1Y":
            start_date = end_date - timedelta(days=365)
        else:  # ALL
            start_date = datetime(2000, 1, 1)

        trades = self.db.query(models.Trade).filter(
            models.Trade.user_id == self.user_id,
            models.Trade.trade_date >= start_date,
            models.Trade.trade_date <= end_date
        ).all()

        return trades

    def calculate_portfolio_metrics(self, period: str = "ALL") -> Dict:
        """Calculate comprehensive portfolio metrics"""
        trades = self.get_trades_for_period(period)

        if not trades:
            return {
                "total_investment": 0,
                "current_value": 0,
                "absolute_returns": 0,
                "percentage_returns": 0,
                "xirr": None,
                "cagr": None,
                "max_drawdown": None,
                "sharpe_ratio": None,
                "win_rate": 0,
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0
            }

        # Calculate basic metrics
        total_investment = 0
        current_value = 0
        cashflows = []
        portfolio_values = []
        daily_returns = []
        winning_trades = 0
        losing_trades = 0

        for trade in trades:
            if trade.trade_type == models.TradeType.BUY:
                total_investment += trade.total_cost
                cashflows.append((trade.trade_date.date(), -trade.total_cost))
            else:  # SELL
                sell_value = trade.quantity * trade.price - trade.brokerage - trade.taxes
                current_value += sell_value
                cashflows.append((trade.trade_date.date(), sell_value))

                # Check if winning or losing trade
                if trade.actual_exit_price:
                    pnl = (trade.actual_exit_price - trade.price) * trade.quantity
                    if pnl > 0:
                        winning_trades += 1
                    else:
                        losing_trades += 1

        # Get current holdings value
        holdings = self.db.query(models.Holding).filter(
            models.Holding.user_id == self.user_id
        ).all()

        for holding in holdings:
            if holding.current_price:
                current_value += holding.quantity * holding.current_price
            else:
                current_value += holding.quantity * holding.average_price

        # Add current value to cashflows for XIRR calculation
        if cashflows:
            cashflows.append((date.today(), current_value))

        # Calculate returns
        absolute_returns = current_value - total_investment
        percentage_returns = (absolute_returns / total_investment * 100) if total_investment > 0 else 0

        # Calculate XIRR
        xirr_value = self.calculate_xirr(cashflows) if len(cashflows) >= 2 else None

        # Calculate CAGR
        if trades:
            first_trade_date = min(trade.trade_date for trade in trades)
            years = (datetime.now() - first_trade_date).days / 365.25
            cagr_value = self.calculate_cagr(total_investment, current_value, years) if years > 0 else None
        else:
            cagr_value = None

        # Calculate win rate
        total_closed_trades = winning_trades + losing_trades
        win_rate = (winning_trades / total_closed_trades * 100) if total_closed_trades > 0 else 0

        return {
            "total_investment": round(total_investment, 2),
            "current_value": round(current_value, 2),
            "absolute_returns": round(absolute_returns, 2),
            "percentage_returns": round(percentage_returns, 2),
            "xirr": xirr_value,
            "cagr": cagr_value,
            "max_drawdown": None,  # Would need historical portfolio values
            "sharpe_ratio": None,  # Would need daily returns
            "win_rate": round(win_rate, 2),
            "total_trades": len(trades),
            "winning_trades": winning_trades,
            "losing_trades": losing_trades
        }

    def get_trade_statistics(self) -> Dict:
        """Get detailed trade statistics"""
        trades = self.db.query(models.Trade).filter(
            models.Trade.user_id == self.user_id
        ).all()

        if not trades:
            return {
                "avg_win": 0,
                "avg_loss": 0,
                "largest_win": 0,
                "largest_loss": 0,
                "avg_holding_period": 0,
                "profit_factor": 0
            }

        wins = []
        losses = []
        holding_periods = []

        for i in range(0, len(trades) - 1, 2):
            if i + 1 < len(trades):
                buy_trade = trades[i]
                sell_trade = trades[i + 1]

                if buy_trade.trade_type == models.TradeType.BUY and sell_trade.trade_type == models.TradeType.SELL:
                    pnl = (sell_trade.price - buy_trade.price) * buy_trade.quantity - buy_trade.brokerage - buy_trade.taxes - sell_trade.brokerage - sell_trade.taxes

                    if pnl > 0:
                        wins.append(pnl)
                    else:
                        losses.append(abs(pnl))

                    holding_period = (sell_trade.trade_date - buy_trade.trade_date).days
                    holding_periods.append(holding_period)

        avg_win = np.mean(wins) if wins else 0
        avg_loss = np.mean(losses) if losses else 0
        largest_win = max(wins) if wins else 0
        largest_loss = max(losses) if losses else 0
        avg_holding_period = np.mean(holding_periods) if holding_periods else 0

        total_wins = sum(wins) if wins else 0
        total_losses = sum(losses) if losses else 0
        profit_factor = (total_wins / total_losses) if total_losses > 0 else 0

        return {
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "largest_win": round(largest_win, 2),
            "largest_loss": round(largest_loss, 2),
            "avg_holding_period": round(avg_holding_period, 1),
            "profit_factor": round(profit_factor, 2)
        }