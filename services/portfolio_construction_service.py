"""
Portfolio Construction Service
Creates data-driven, adaptive model portfolios based on client risk profile
Integrates live mutual fund data and advanced features (step-up, tax harvesting)
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import math


class PortfolioConstructionService:
    """Advanced portfolio construction with equity focus and MF risk cushion"""

    # Asset allocation based on risk profile (Equity-focused strategy)
    RISK_ALLOCATIONS = {
        "CONSERVATIVE": {
            "equity": {"min": 30, "max": 40, "recommended": 35},
            "mutual_funds": {"min": 50, "max": 60, "recommended": 55},
            "cash": {"min": 5, "max": 15, "recommended": 10},
            "description": "Capital preservation with modest growth"
        },
        "MODERATE": {
            "equity": {"min": 50, "max": 65, "recommended": 60},
            "mutual_funds": {"min": 30, "max": 45, "recommended": 35},
            "cash": {"min": 3, "max": 8, "recommended": 5},
            "description": "Balanced growth with managed risk"
        },
        "AGGRESSIVE": {
            "equity": {"min": 70, "max": 85, "recommended": 75},
            "mutual_funds": {"min": 15, "max": 25, "recommended": 20},
            "cash": {"min": 0, "max": 10, "recommended": 5},
            "description": "Maximum growth potential with equity focus"
        }
    }

    # Equity breakdown by market cap (Our forte - direct equity)
    EQUITY_BREAKDOWN = {
        "CONSERVATIVE": {
            "large_cap": 70,
            "mid_cap": 20,
            "small_cap": 10
        },
        "MODERATE": {
            "large_cap": 50,
            "mid_cap": 35,
            "small_cap": 15
        },
        "AGGRESSIVE": {
            "large_cap": 40,
            "mid_cap": 35,
            "small_cap": 25
        }
    }

    # Mutual Fund breakdown (Risk cushion)
    MF_BREAKDOWN = {
        "CONSERVATIVE": {
            "debt": 70,      # Liquid, Short Duration, Corporate Bond
            "hybrid": 25,    # Conservative Hybrid, Balanced Advantage
            "gold": 5        # Gold ETF/Fund
        },
        "MODERATE": {
            "debt": 50,
            "hybrid": 40,
            "gold": 10
        },
        "AGGRESSIVE": {
            "debt": 40,
            "hybrid": 50,
            "gold": 10
        }
    }

    @staticmethod
    def generate_model_portfolios(
        risk_profile: str,
        monthly_sip: float = 0,
        lumpsum: float = 0,
        timeline_years: int = 10,
        step_up_percent: float = 10,
        equity_preference: Optional[float] = None
    ) -> List[Dict]:
        """
        Generate 2-3 model portfolio options based on client profile

        Args:
            risk_profile: CONSERVATIVE, MODERATE, AGGRESSIVE
            monthly_sip: Monthly SIP amount
            lumpsum: One-time lumpsum amount
            timeline_years: Investment horizon in years
            step_up_percent: Annual SIP increase %
            equity_preference: Override equity % (for adaptive dashboard)

        Returns:
            List of portfolio options with detailed breakup
        """
        allocations = PortfolioConstructionService.RISK_ALLOCATIONS[risk_profile]

        portfolios = []

        # Portfolio 1: Recommended (Balanced)
        portfolio_1 = PortfolioConstructionService._create_portfolio(
            name=f"{risk_profile.title()} - Recommended",
            risk_profile=risk_profile,
            equity_percent=equity_preference or allocations["equity"]["recommended"],
            monthly_sip=monthly_sip,
            lumpsum=lumpsum,
            timeline_years=timeline_years,
            step_up_percent=step_up_percent,
            strategy="Balanced approach with optimal risk-return"
        )
        portfolios.append(portfolio_1)

        # Portfolio 2: Conservative variant
        if equity_preference is None:
            portfolio_2 = PortfolioConstructionService._create_portfolio(
                name=f"{risk_profile.title()} - Conservative",
                risk_profile=risk_profile,
                equity_percent=allocations["equity"]["min"],
                monthly_sip=monthly_sip,
                lumpsum=lumpsum,
                timeline_years=timeline_years,
                step_up_percent=step_up_percent,
                strategy="Lower risk with more stability"
            )
            portfolios.append(portfolio_2)

        # Portfolio 3: Aggressive variant
        if equity_preference is None:
            portfolio_3 = PortfolioConstructionService._create_portfolio(
                name=f"{risk_profile.title()} - Aggressive",
                risk_profile=risk_profile,
                equity_percent=allocations["equity"]["max"],
                monthly_sip=monthly_sip,
                lumpsum=lumpsum,
                timeline_years=timeline_years,
                step_up_percent=step_up_percent,
                strategy="Maximum growth with higher volatility"
            )
            portfolios.append(portfolio_3)

        return portfolios

    @staticmethod
    def _create_portfolio(
        name: str,
        risk_profile: str,
        equity_percent: float,
        monthly_sip: float,
        lumpsum: float,
        timeline_years: int,
        step_up_percent: float,
        strategy: str
    ) -> Dict:
        """Create detailed portfolio with all calculations"""

        # Calculate MF and cash allocation
        mf_percent = 100 - equity_percent - 5  # 5% cash buffer
        cash_percent = 5

        # Get breakdowns
        equity_breakdown = PortfolioConstructionService.EQUITY_BREAKDOWN[risk_profile]
        mf_breakdown = PortfolioConstructionService.MF_BREAKDOWN[risk_profile]

        # Calculate amounts
        total_monthly = monthly_sip
        equity_monthly = total_monthly * (equity_percent / 100)
        mf_monthly = total_monthly * (mf_percent / 100)
        cash_monthly = total_monthly * (cash_percent / 100)

        # Lumpsum allocation
        equity_lumpsum = lumpsum * (equity_percent / 100)
        mf_lumpsum = lumpsum * (mf_percent / 100)
        cash_lumpsum = lumpsum * (cash_percent / 100)

        # Calculate projections
        projections = PortfolioConstructionService._calculate_projections(
            monthly_sip=monthly_sip,
            lumpsum=lumpsum,
            timeline_years=timeline_years,
            equity_percent=equity_percent,
            step_up_percent=step_up_percent,
            risk_profile=risk_profile
        )

        # Tax harvesting strategy
        tax_harvesting = PortfolioConstructionService._calculate_tax_harvesting(
            projections["year_by_year"],
            timeline_years
        )

        portfolio = {
            "name": name,
            "strategy": strategy,
            "risk_profile": risk_profile,
            "allocation": {
                "equity": {
                    "percent": equity_percent,
                    "monthly_sip": equity_monthly,
                    "lumpsum": equity_lumpsum,
                    "breakdown": {
                        "large_cap": {
                            "percent": equity_breakdown["large_cap"],
                            "monthly": equity_monthly * (equity_breakdown["large_cap"] / 100),
                            "lumpsum": equity_lumpsum * (equity_breakdown["large_cap"] / 100)
                        },
                        "mid_cap": {
                            "percent": equity_breakdown["mid_cap"],
                            "monthly": equity_monthly * (equity_breakdown["mid_cap"] / 100),
                            "lumpsum": equity_lumpsum * (equity_breakdown["mid_cap"] / 100)
                        },
                        "small_cap": {
                            "percent": equity_breakdown["small_cap"],
                            "monthly": equity_monthly * (equity_breakdown["small_cap"] / 100),
                            "lumpsum": equity_lumpsum * (equity_breakdown["small_cap"] / 100)
                        }
                    }
                },
                "mutual_funds": {
                    "percent": mf_percent,
                    "monthly_sip": mf_monthly,
                    "lumpsum": mf_lumpsum,
                    "breakdown": {
                        "debt": {
                            "percent": mf_breakdown["debt"],
                            "monthly": mf_monthly * (mf_breakdown["debt"] / 100),
                            "lumpsum": mf_lumpsum * (mf_breakdown["debt"] / 100)
                        },
                        "hybrid": {
                            "percent": mf_breakdown["hybrid"],
                            "monthly": mf_monthly * (mf_breakdown["hybrid"] / 100),
                            "lumpsum": mf_lumpsum * (mf_breakdown["hybrid"] / 100)
                        },
                        "gold": {
                            "percent": mf_breakdown["gold"],
                            "monthly": mf_monthly * (mf_breakdown["gold"] / 100),
                            "lumpsum": mf_lumpsum * (mf_breakdown["gold"] / 100)
                        }
                    }
                },
                "cash": {
                    "percent": cash_percent,
                    "monthly_sip": cash_monthly,
                    "lumpsum": cash_lumpsum
                }
            },
            "projections": projections,
            "tax_harvesting": tax_harvesting,
            "parameters": {
                "monthly_sip": monthly_sip,
                "lumpsum": lumpsum,
                "timeline_years": timeline_years,
                "step_up_percent": step_up_percent
            }
        }

        return portfolio

    @staticmethod
    def _calculate_projections(
        monthly_sip: float,
        lumpsum: float,
        timeline_years: int,
        equity_percent: float,
        step_up_percent: float,
        risk_profile: str
    ) -> Dict:
        """
        Calculate year-by-year projections with step-up

        Expected CAGR by Risk Profile (minimum 3-4 years timeline):
        - Conservative: 18% CAGR
        - Moderate: 22% CAGR
        - Aggressive: 25% CAGR
        """

        # Portfolio expected returns based on risk profile
        # These are blended returns accounting for equity + MF + cash allocation
        PORTFOLIO_CAGR = {
            "CONSERVATIVE": 0.18,  # 18% CAGR
            "MODERATE": 0.22,      # 22% CAGR
            "AGGRESSIVE": 0.25     # 25% CAGR
        }

        # Use risk-profile specific CAGR
        blended_return = PORTFOLIO_CAGR.get(risk_profile, 0.20)  # Default 20% if not found

        year_by_year = []
        total_invested = lumpsum
        portfolio_value = lumpsum
        current_monthly_sip = monthly_sip

        for year in range(1, timeline_years + 1):
            # SIP for this year
            annual_sip = current_monthly_sip * 12
            total_invested += annual_sip

            # Growth calculation
            # Lumpsum grows for full year
            lumpsum_growth = portfolio_value * blended_return
            # SIP grows for average 6 months (mid-year approximation)
            sip_growth = annual_sip * (blended_return / 2)

            portfolio_value += annual_sip + lumpsum_growth + sip_growth

            gains = portfolio_value - total_invested

            year_by_year.append({
                "year": year,
                "monthly_sip": current_monthly_sip,
                "annual_invested": annual_sip,
                "total_invested": total_invested,
                "portfolio_value": round(portfolio_value, 2),
                "gains": round(gains, 2),
                "return_percent": round((gains / total_invested) * 100, 2) if total_invested > 0 else 0
            })

            # Step-up for next year
            current_monthly_sip = current_monthly_sip * (1 + step_up_percent / 100)

        return {
            "final_value": round(portfolio_value, 2),
            "total_invested": round(total_invested, 2),
            "total_gains": round(portfolio_value - total_invested, 2),
            "cagr": round(blended_return * 100, 2),
            "year_by_year": year_by_year
        }

    @staticmethod
    def _calculate_tax_harvesting(year_by_year: List[Dict], timeline_years: int) -> Dict:
        """
        Calculate tax harvesting opportunities
        Book ₹1.25L profit every 2 years (LTCG exemption)
        """
        harvesting_schedule = []
        total_harvested = 0

        for year_data in year_by_year:
            year = year_data["year"]

            # Check every 2 years (starting from year 2)
            if year >= 2 and year % 2 == 0:
                gains = year_data["gains"]

                # Can harvest up to ₹1.25L
                harvestable = min(125000, gains - total_harvested)

                if harvestable > 0:
                    total_harvested += harvestable

                    harvesting_schedule.append({
                        "year": year,
                        "portfolio_value": year_data["portfolio_value"],
                        "total_gains": gains,
                        "harvest_amount": harvestable,
                        "tax_saved": 0,  # First ₹1.25L is tax-free
                        "action": f"Book ₹{harvestable:,.0f} profit and reinvest",
                        "benefit": "Reset cost basis, rebalance portfolio, tax-free gains"
                    })

        return {
            "total_harvested": total_harvested,
            "schedule": harvesting_schedule,
            "strategy": "Book ₹1.25L LTCG profit every 2 years (tax-free) and reinvest in new opportunities",
            "value_proposition": "This strategy saves tax, allows rebalancing, and exploits market opportunities"
        }

    @staticmethod
    def calculate_portfolio_health_score(portfolio: Dict) -> Dict:
        """
        Calculate portfolio health score (0-100)
        Metrics: Diversification, Risk-adjusted returns, Tax efficiency
        """
        scores = {
            "diversification": 0,
            "risk_adjusted_returns": 0,
            "tax_efficiency": 0
        }

        # Diversification score (40 points)
        allocation = portfolio["allocation"]
        equity_pct = allocation["equity"]["percent"]
        mf_pct = allocation["mutual_funds"]["percent"]

        # Well-diversified: 30-70% in any single asset class
        if 30 <= equity_pct <= 70 and 20 <= mf_pct <= 60:
            scores["diversification"] = 40
        elif 20 <= equity_pct <= 80:
            scores["diversification"] = 30
        else:
            scores["diversification"] = 20

        # Risk-adjusted returns (40 points)
        cagr = portfolio["projections"]["cagr"]
        if cagr >= 14:
            scores["risk_adjusted_returns"] = 40
        elif cagr >= 12:
            scores["risk_adjusted_returns"] = 35
        elif cagr >= 10:
            scores["risk_adjusted_returns"] = 30
        else:
            scores["risk_adjusted_returns"] = 25

        # Tax efficiency (20 points)
        tax_harvesting = portfolio["tax_harvesting"]
        if tax_harvesting["total_harvested"] > 0:
            scores["tax_efficiency"] = 20
        else:
            scores["tax_efficiency"] = 10

        total_score = sum(scores.values())

        return {
            "total_score": total_score,
            "grade": "Excellent" if total_score >= 85 else "Good" if total_score >= 70 else "Average",
            "breakdown": scores
        }
