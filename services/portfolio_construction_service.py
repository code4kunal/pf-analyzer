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

    # SEBI-Compliant Mandatory Disclosures
    MANDATORY_DISCLOSURES = {
        "market_risk": "Investments in securities market are subject to market risks. Read all related documents carefully before investing.",
        "past_performance": "Past performance is not indicative of future returns. Returns may vary based on market conditions.",
        "equity_disclaimer": "Direct equity investments carry higher risk and are subject to market volatility. The projected returns of 18-25% on equity are based on historical performance and active stock selection expertise. Actual returns may differ significantly.",
        "no_guarantee": "Returns are not guaranteed and will depend on various factors including market conditions, economic factors, and stock selection.",
        "mutual_fund_risk": "Mutual fund investments are subject to market risks. Please read all scheme-related documents carefully.",
        "tax_disclaimer": "Tax benefits are subject to conditions under the Income Tax Act, 1961. Tax laws are subject to change. Please consult your tax advisor.",
        "suitability": "This portfolio is designed based on your risk profile and investment goals. Please ensure you have adequate emergency funds and insurance coverage before investing.",
        "professional_advice": "This is a model portfolio recommendation. Please consult with a SEBI-registered investment advisor for personalized advice."
    }

    # Suitability Assessment - Financial Foundation Check
    @staticmethod
    def assess_investment_suitability(client_data: Dict) -> Dict:
        """
        Check if client has proper financial foundation before investing

        Explanation to clients:
        "Before investing in markets, we need to ensure you have safety nets in place:
        1. Emergency Fund: 6-12 months of expenses in liquid funds
        2. Term Insurance: 15-20x your annual income
        3. Health Insurance: Adequate family floater (₹10L minimum)
        4. Debt Management: Monthly EMI should be <40% of income"
        """

        checks = {
            "emergency_fund": {"status": "NOT_CHECKED", "message": ""},
            "term_insurance": {"status": "NOT_CHECKED", "message": ""},
            "health_insurance": {"status": "NOT_CHECKED", "message": ""},
            "debt_ratio": {"status": "NOT_CHECKED", "message": ""},
            "overall_suitable": True,
            "recommendations": []
        }

        # 1. Emergency Fund Check
        monthly_expenses = client_data.get("monthly_expenses", 0)
        existing_liquid = client_data.get("emergency_fund", 0)

        if monthly_expenses > 0:
            required_emergency = monthly_expenses * 6  # 6 months minimum
            recommended_emergency = monthly_expenses * 12  # 12 months ideal

            if existing_liquid >= recommended_emergency:
                checks["emergency_fund"]["status"] = "EXCELLENT"
                checks["emergency_fund"]["message"] = f"Emergency fund adequate: ₹{existing_liquid:,.0f} (12+ months covered) ✓"
            elif existing_liquid >= required_emergency:
                checks["emergency_fund"]["status"] = "ADEQUATE"
                checks["emergency_fund"]["message"] = f"Emergency fund present: ₹{existing_liquid:,.0f} (6-12 months) ✓"
            else:
                checks["emergency_fund"]["status"] = "INSUFFICIENT"
                checks["emergency_fund"]["message"] = f"⚠️ Emergency fund low: ₹{existing_liquid:,.0f}. Need ₹{required_emergency:,.0f} minimum (6 months expenses)"
                checks["overall_suitable"] = False
                checks["recommendations"].append(f"Build emergency fund to ₹{required_emergency:,.0f} before equity investment")

        # 2. Term Insurance Check
        annual_income = client_data.get("annual_income", 0)
        term_coverage = client_data.get("term_insurance_coverage", 0)

        if annual_income > 0:
            required_coverage = annual_income * 15  # 15x income minimum
            recommended_coverage = annual_income * 20  # 20x income ideal

            if term_coverage >= recommended_coverage:
                checks["term_insurance"]["status"] = "EXCELLENT"
                checks["term_insurance"]["message"] = f"Term insurance excellent: ₹{term_coverage:,.0f} (20x income) ✓"
            elif term_coverage >= required_coverage:
                checks["term_insurance"]["status"] = "ADEQUATE"
                checks["term_insurance"]["message"] = f"Term insurance adequate: ₹{term_coverage:,.0f} (15-20x income) ✓"
            else:
                checks["term_insurance"]["status"] = "INSUFFICIENT"
                checks["term_insurance"]["message"] = f"⚠️ Term insurance low: ₹{term_coverage:,.0f}. Need ₹{required_coverage:,.0f} minimum (15x income)"
                checks["overall_suitable"] = False
                checks["recommendations"].append(f"Increase term insurance to ₹{required_coverage:,.0f} before taking equity risk")

        # 3. Health Insurance Check
        family_size = client_data.get("family_members", 1)
        health_coverage = client_data.get("health_insurance_coverage", 0)

        required_health = max(500000, family_size * 500000)  # ₹5L per person minimum
        recommended_health = max(1000000, family_size * 500000)  # ₹10L minimum or ₹5L per person

        if health_coverage >= recommended_health:
            checks["health_insurance"]["status"] = "EXCELLENT"
            checks["health_insurance"]["message"] = f"Health insurance excellent: ₹{health_coverage:,.0f} ✓"
        elif health_coverage >= required_health:
            checks["health_insurance"]["status"] = "ADEQUATE"
            checks["health_insurance"]["message"] = f"Health insurance adequate: ₹{health_coverage:,.0f} ✓"
        else:
            checks["health_insurance"]["status"] = "INSUFFICIENT"
            checks["health_insurance"]["message"] = f"⚠️ Health insurance low: ₹{health_coverage:,.0f}. Need ₹{required_health:,.0f} minimum"
            checks["recommendations"].append(f"Get health insurance of at least ₹{required_health:,.0f}")

        # 4. Debt Ratio Check
        monthly_income = client_data.get("monthly_income", 0)
        monthly_emi = client_data.get("monthly_emi", 0)

        if monthly_income > 0 and monthly_emi > 0:
            debt_ratio = (monthly_emi / monthly_income) * 100

            if debt_ratio < 30:
                checks["debt_ratio"]["status"] = "EXCELLENT"
                checks["debt_ratio"]["message"] = f"Debt ratio healthy: {debt_ratio:.1f}% (EMI/Income) ✓"
            elif debt_ratio < 40:
                checks["debt_ratio"]["status"] = "ACCEPTABLE"
                checks["debt_ratio"]["message"] = f"Debt ratio acceptable: {debt_ratio:.1f}% (EMI/Income) ✓"
            else:
                checks["debt_ratio"]["status"] = "HIGH"
                checks["debt_ratio"]["message"] = f"⚠️ Debt ratio high: {debt_ratio:.1f}% (EMI/Income). Should be <40%"
                checks["recommendations"].append("Reduce debt burden before increasing investments")

        # Final recommendation
        if checks["overall_suitable"]:
            checks["final_recommendation"] = "✓ You have a strong financial foundation. Ready to invest in equity markets."
        else:
            checks["final_recommendation"] = "⚠️ Please address the gaps in your financial foundation before investing heavily in equity. We can help you with a phased approach."

        return checks

    # Age-Based Equity Allocation Guidelines
    # Rule: Younger investors can take more equity risk due to longer time horizon
    @staticmethod
    def calculate_age_adjusted_equity(age: int, risk_profile: str, timeline_years: int) -> Dict:
        """
        Calculate age-appropriate equity allocation

        Logic explained to clients:
        - Younger age (20-30): Can handle 70-80% equity (long recovery time)
        - Middle age (30-50): 50-70% equity (balanced approach)
        - Nearing retirement (50-60): 30-50% equity (capital preservation)
        - Post-retirement (60+): 20-40% equity (income focus)

        Modified by:
        - Risk profile (Conservative reduces by 20%, Aggressive increases by 10%)
        - Timeline (Short timeline reduces equity, long timeline allows more)
        """
        # Base allocation using "100 - age" rule
        base_equity = min(100 - age, 85)  # Max 85% regardless of age

        # Risk profile adjustment
        RISK_ADJUSTMENTS = {
            "CONSERVATIVE": 0.75,  # Reduce by 25%
            "MODERATE": 0.95,      # Reduce by 5%
            "AGGRESSIVE": 1.15     # Increase by 15%
        }

        adjusted_equity = base_equity * RISK_ADJUSTMENTS.get(risk_profile, 1.0)

        # Timeline adjustment
        if timeline_years < 3:
            adjusted_equity *= 0.4  # Very short timeline - reduce significantly
            recommendation = "Short timeline detected. Reducing equity allocation for capital safety."
        elif timeline_years < 5:
            adjusted_equity *= 0.7  # Short-medium timeline
            recommendation = "Medium-short timeline. Balanced allocation recommended."
        elif timeline_years >= 10:
            adjusted_equity = min(adjusted_equity * 1.1, 85)  # Long timeline - can increase
            recommendation = "Long investment horizon allows higher equity allocation."
        else:
            recommendation = "Standard allocation based on risk profile."

        # Final bounds
        final_equity = max(20, min(adjusted_equity, 85))  # Between 20-85%

        return {
            "recommended_equity": round(final_equity, 1),
            "age_factor": age,
            "base_allocation": round(base_equity, 1),
            "risk_adjusted": round(adjusted_equity, 1),
            "timeline_impact": timeline_years,
            "recommendation": recommendation,
            "explanation": f"For age {age} with {risk_profile} risk profile and {timeline_years}-year timeline: {round(final_equity, 1)}% equity recommended"
        }

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

        RETURN ASSUMPTIONS (Explained to clients):

        DIRECT EQUITY (Our Expertise - 70-80% allocation):
        - Conservative: 18% CAGR (Large-cap focused, quality stocks)
        - Moderate: 22% CAGR (Balanced large/mid-cap, growth stocks)
        - Aggressive: 25% CAGR (Multi-cap, high-growth opportunities)

        MUTUAL FUNDS (Risk Cushion - 20-30% allocation):
        - Debt Funds: 8-9% CAGR (Corporate bonds, short duration)
        - Hybrid Funds: 10-12% CAGR (Balanced advantage, multi-asset)
        - Gold Funds: 8-10% CAGR (Hedge against volatility)

        BLENDED PORTFOLIO RETURN:
        - Weighted average based on allocation
        - Conservative: ~16% (35% equity at 18% + 55% MF at 9% + 10% cash at 6%)
        - Moderate: ~18% (60% equity at 22% + 35% MF at 10% + 5% cash at 6%)
        - Aggressive: ~21% (75% equity at 25% + 20% MF at 11% + 5% cash at 6%)
        """

        # Asset class expected returns (explained clearly to clients)
        EQUITY_RETURNS = {
            "CONSERVATIVE": 0.18,  # 18% - Direct equity (our expertise)
            "MODERATE": 0.22,      # 22% - Direct equity
            "AGGRESSIVE": 0.25     # 25% - Direct equity
        }

        MF_RETURNS = {
            "CONSERVATIVE": 0.09,  # 9% - Debt-heavy MF mix
            "MODERATE": 0.10,      # 10% - Balanced MF mix
            "AGGRESSIVE": 0.11     # 11% - Hybrid-heavy MF mix
        }

        CASH_RETURN = 0.06  # 6% - Liquid funds/savings

        # Calculate blended return based on actual allocation
        equity_return = EQUITY_RETURNS[risk_profile]
        mf_return = MF_RETURNS[risk_profile]
        mf_percent = 95 - equity_percent  # Remaining after equity (5% cash)

        # Blended return = weighted average
        blended_return = (
            (equity_percent / 100) * equity_return +
            (mf_percent / 100) * mf_return +
            (5 / 100) * CASH_RETURN
        )

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
            "year_by_year": year_by_year,
            "return_breakdown": {
                "equity_return": round(equity_return * 100, 2),
                "equity_allocation": equity_percent,
                "mf_return": round(mf_return * 100, 2),
                "mf_allocation": mf_percent,
                "cash_return": round(CASH_RETURN * 100, 2),
                "cash_allocation": 5,
                "blended_return": round(blended_return * 100, 2),
                "explanation": f"Blended Return = ({equity_percent}% × {round(equity_return*100,1)}%) + ({mf_percent}% × {round(mf_return*100,1)}%) + (5% × {round(CASH_RETURN*100,1)}%) = {round(blended_return*100,1)}%"
            }
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
    def calculate_scenario_projections(
        monthly_sip: float,
        lumpsum: float,
        timeline_years: int,
        equity_percent: float,
        step_up_percent: float,
        risk_profile: str
    ) -> Dict:
        """
        Calculate 3 scenarios: Optimistic, Expected, Pessimistic

        Client Explanation:
        - EXPECTED: Based on our historical performance and market averages
        - OPTIMISTIC: If markets perform well and stock picking excels (Best Case)
        - PESSIMISTIC: If markets decline or face headwinds (Worst Case)

        This gives you a realistic range of possible outcomes
        """

        # Get base returns
        BASE_EQUITY_RETURNS = {
            "CONSERVATIVE": 0.18,
            "MODERATE": 0.22,
            "AGGRESSIVE": 0.25
        }

        BASE_MF_RETURNS = {
            "CONSERVATIVE": 0.09,
            "MODERATE": 0.10,
            "AGGRESSIVE": 0.11
        }

        base_equity = BASE_EQUITY_RETURNS[risk_profile]
        base_mf = BASE_MF_RETURNS[risk_profile]

        # Scenario multipliers
        scenarios = {
            "expected": {
                "equity_multiplier": 1.0,
                "mf_multiplier": 1.0,
                "description": "Based on historical averages and our active management"
            },
            "optimistic": {
                "equity_multiplier": 1.25,  # 25% higher (Bull market + excellent picks)
                "mf_multiplier": 1.15,      # 15% higher
                "description": "Strong bull market with excellent stock selection"
            },
            "pessimistic": {
                "equity_multiplier": 0.65,  # 35% lower (Bear market/corrections)
                "mf_multiplier": 0.85,      # 15% lower
                "description": "Market corrections or bear phase"
            }
        }

        results = {}

        for scenario_name, scenario_data in scenarios.items():
            # Adjusted returns
            equity_return = base_equity * scenario_data["equity_multiplier"]
            mf_return = base_mf * scenario_data["mf_multiplier"]
            cash_return = 0.06  # Stays constant

            mf_percent = 95 - equity_percent
            blended_return = (
                (equity_percent / 100) * equity_return +
                (mf_percent / 100) * mf_return +
                (5 / 100) * cash_return
            )

            # Calculate final value with this return
            portfolio_value = lumpsum
            total_invested = lumpsum
            current_sip = monthly_sip

            for year in range(1, timeline_years + 1):
                annual_sip = current_sip * 12
                total_invested += annual_sip

                lumpsum_growth = portfolio_value * blended_return
                sip_growth = annual_sip * (blended_return / 2)

                portfolio_value += annual_sip + lumpsum_growth + sip_growth
                current_sip = current_sip * (1 + step_up_percent / 100)

            results[scenario_name] = {
                "final_value": round(portfolio_value, 2),
                "total_invested": round(total_invested, 2),
                "total_gains": round(portfolio_value - total_invested, 2),
                "cagr": round(blended_return * 100, 2),
                "equity_return": round(equity_return * 100, 2),
                "description": scenario_data["description"]
            }

        # Calculate range
        value_range = results["optimistic"]["final_value"] - results["pessimistic"]["final_value"]

        return {
            "scenarios": results,
            "range_analysis": {
                "best_case": results["optimistic"]["final_value"],
                "most_likely": results["expected"]["final_value"],
                "worst_case": results["pessimistic"]["final_value"],
                "range": round(value_range, 2),
                "explanation": f"Your portfolio value can range from ₹{results['pessimistic']['final_value']:,.0f} to ₹{results['optimistic']['final_value']:,.0f}, with most likely outcome around ₹{results['expected']['final_value']:,.0f}"
            }
        }

    @staticmethod
    def generate_rebalancing_strategy(risk_profile: str, timeline_years: int) -> Dict:
        """
        Generate portfolio rebalancing recommendations

        Explanation to clients:
        - Markets move up and down, changing your asset allocation
        - If equity grows too much, you're taking more risk than intended
        - If equity falls, you're too conservative and missing growth
        - Rebalancing = selling high, buying low automatically
        """

        if timeline_years < 3:
            frequency = "Quarterly"
            drift_tolerance = 3
            explanation = "Short timeline requires close monitoring and frequent rebalancing"
        elif timeline_years < 7:
            frequency = "Semi-annually"
            drift_tolerance = 5
            explanation = "Medium timeline allows moderate drift before rebalancing"
        else:
            frequency = "Annually"
            drift_tolerance = 7
            explanation = "Long timeline allows more flexibility, review once a year"

        target_allocation = PortfolioConstructionService.RISK_ALLOCATIONS[risk_profile]

        return {
            "frequency": frequency,
            "drift_tolerance_percent": drift_tolerance,
            "target_equity": target_allocation["equity"]["recommended"],
            "target_mf": target_allocation["mutual_funds"]["recommended"],
            "target_cash": target_allocation["cash"]["recommended"],
            "rebalancing_triggers": [
                f"Review portfolio {frequency.lower()}",
                f"Rebalance if equity allocation drifts by >{drift_tolerance}%",
                "Always rebalance during major market moves (>20% change)",
                "Use tax-loss harvesting opportunities when rebalancing"
            ],
            "process": [
                "1. Calculate current allocation (%)",
                "2. Compare with target allocation",
                f"3. If drift > {drift_tolerance}%, sell overweight and buy underweight",
                "4. Use rebalancing to book profits and average down losses",
                "5. Combine with tax harvesting for efficiency"
            ],
            "example": f"If equity grows to {target_allocation['equity']['recommended'] + drift_tolerance + 5}% (target: {target_allocation['equity']['recommended']}%), sell some equity and buy MF/debt to restore balance",
            "benefit": "Rebalancing enforces discipline: 'Sell high, buy low' automatically without emotions"
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
