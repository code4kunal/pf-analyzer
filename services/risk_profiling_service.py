"""
Risk Profiling Questionnaire Service
Handles risk assessment questionnaire, scoring, and recommendations
"""

from typing import List, Dict, Optional
from models import RiskCategory
from schemas import RiskProfileQuestionAnswer

class RiskProfilingService:
    """Service for risk assessment and profiling"""

    # Enhanced Risk Assessment Questionnaire with Detailed Explanations
    QUESTIONNAIRE = [
        {
            "question_id": "Q1",
            "question_text": "What is your age group?",
            "explanation": "Younger investors typically have more time to recover from market downturns and can take higher risks. As you approach retirement, capital preservation becomes more important.",
            "help_text": "Age helps determine your investment horizon - the longer you have until retirement, the more time your investments have to grow and recover from market volatility.",
            "options": [
                {
                    "answer": "Below 35 years",
                    "score": 4,
                    "description": "30+ years to retirement - You have significant time to ride out market cycles and benefit from compounding"
                },
                {
                    "answer": "35-45 years",
                    "score": 3,
                    "description": "15-25 years to retirement - Good time horizon for balanced growth with moderate risk"
                },
                {
                    "answer": "46-55 years",
                    "score": 2,
                    "description": "10-15 years to retirement - Time to gradually reduce risk and preserve capital"
                },
                {
                    "answer": "Above 55 years",
                    "score": 1,
                    "description": "Near or in retirement - Focus should shift to capital preservation and steady income"
                }
            ]
        },
        {
            "question_id": "Q2",
            "question_text": "What is your investment time horizon?",
            "options": [
                {"answer": "More than 10 years", "score": 4},
                {"answer": "5-10 years", "score": 3},
                {"answer": "3-5 years", "score": 2},
                {"answer": "Less than 3 years", "score": 1}
            ]
        },
        {
            "question_id": "Q3",
            "question_text": "What percentage of your monthly income can you invest?",
            "options": [
                {"answer": "More than 30%", "score": 4},
                {"answer": "20-30%", "score": 3},
                {"answer": "10-20%", "score": 2},
                {"answer": "Less than 10%", "score": 1}
            ]
        },
        {
            "question_id": "Q4",
            "question_text": "How would you describe your knowledge of investments?",
            "options": [
                {"answer": "Excellent - I actively manage my portfolio", "score": 4},
                {"answer": "Good - I understand stocks, bonds, and mutual funds", "score": 3},
                {"answer": "Limited - I understand basic concepts", "score": 2},
                {"answer": "None - I'm new to investing", "score": 1}
            ]
        },
        {
            "question_id": "Q5",
            "question_text": "What is your primary investment objective?",
            "options": [
                {"answer": "Aggressive growth - maximize returns", "score": 4},
                {"answer": "Growth - higher returns with moderate risk", "score": 3},
                {"answer": "Balanced - stable returns with some risk", "score": 2},
                {"answer": "Capital preservation - minimize risk", "score": 1}
            ]
        },
        {
            "question_id": "Q6",
            "question_text": "If your portfolio value dropped by 20% in a year, you would:",
            "options": [
                {"answer": "Invest more - it's a buying opportunity", "score": 4},
                {"answer": "Hold on - markets will recover", "score": 3},
                {"answer": "Worry but wait - give it some time", "score": 2},
                {"answer": "Sell immediately - I can't bear losses", "score": 1}
            ]
        },
        {
            "question_id": "Q7",
            "question_text": "What level of fluctuation in returns can you tolerate?",
            "options": [
                {"answer": "High fluctuation for potentially higher returns", "score": 4},
                {"answer": "Moderate fluctuation for moderate returns", "score": 3},
                {"answer": "Low fluctuation for stable returns", "score": 2},
                {"answer": "No fluctuation - I want guaranteed returns", "score": 1}
            ]
        },
        {
            "question_id": "Q8",
            "question_text": "Do you have any existing liabilities (loans, EMIs)?",
            "options": [
                {"answer": "No liabilities", "score": 4},
                {"answer": "Minimal liabilities (< 20% of income)", "score": 3},
                {"answer": "Moderate liabilities (20-40% of income)", "score": 2},
                {"answer": "High liabilities (> 40% of income)", "score": 1}
            ]
        },
        {
            "question_id": "Q9",
            "question_text": "How stable is your current income source?",
            "options": [
                {"answer": "Very stable - salaried with job security", "score": 4},
                {"answer": "Stable - salaried but some uncertainty", "score": 3},
                {"answer": "Moderately stable - business/self-employed", "score": 2},
                {"answer": "Unstable - irregular income", "score": 1}
            ]
        },
        {
            "question_id": "Q10",
            "question_text": "Do you have an emergency fund (6 months expenses)?",
            "options": [
                {"answer": "Yes, more than 12 months", "score": 4},
                {"answer": "Yes, 6-12 months", "score": 3},
                {"answer": "Partial - 3-6 months", "score": 2},
                {"answer": "No emergency fund", "score": 1}
            ]
        }
    ]

    @staticmethod
    def get_questionnaire() -> List[Dict]:
        """Get the complete risk assessment questionnaire"""
        return RiskProfilingService.QUESTIONNAIRE

    @staticmethod
    def calculate_risk_score(responses: List[RiskProfileQuestionAnswer]) -> int:
        """
        Calculate total risk score from questionnaire responses

        Args:
            responses: List of question-answer pairs with scores

        Returns:
            Total risk score (10-40)
        """
        total_score = sum(response.score for response in responses)

        # Validate score range
        if total_score < 10:
            total_score = 10
        elif total_score > 40:
            total_score = 40

        return total_score

    @staticmethod
    def determine_risk_category(total_score: int) -> RiskCategory:
        """
        Determine risk category based on total score

        Score Ranges:
        - 10-18: CONSERVATIVE (Low risk tolerance)
        - 19-28: MODERATE (Medium risk tolerance)
        - 29-40: AGGRESSIVE (High risk tolerance)

        Args:
            total_score: Total score from questionnaire

        Returns:
            RiskCategory enum
        """
        if total_score <= 18:
            return RiskCategory.CONSERVATIVE
        elif total_score <= 28:
            return RiskCategory.MODERATE
        else:
            return RiskCategory.AGGRESSIVE

    @staticmethod
    def get_asset_allocation_recommendation(risk_category: RiskCategory) -> Dict[str, int]:
        """
        Get recommended asset allocation based on risk category

        Asset Allocation Guidelines:

        CONSERVATIVE:
        - Equity: 20-30%
        - Debt: 60-70%
        - Gold: 10%

        MODERATE:
        - Equity: 50-60%
        - Debt: 30-40%
        - Gold: 10%

        AGGRESSIVE:
        - Equity: 70-80%
        - Debt: 10-20%
        - Gold: 10%

        Args:
            risk_category: RiskCategory enum

        Returns:
            Dictionary with equity, debt, and gold percentages
        """
        allocations = {
            RiskCategory.CONSERVATIVE: {
                "equity": 25,
                "debt": 65,
                "gold": 10,
                "equity_range": "20-30%",
                "debt_range": "60-70%",
                "gold_range": "10%"
            },
            RiskCategory.MODERATE: {
                "equity": 55,
                "debt": 35,
                "gold": 10,
                "equity_range": "50-60%",
                "debt_range": "30-40%",
                "gold_range": "10%"
            },
            RiskCategory.AGGRESSIVE: {
                "equity": 75,
                "debt": 15,
                "gold": 10,
                "equity_range": "70-80%",
                "debt_range": "10-20%",
                "gold_range": "10%"
            }
        }

        return allocations.get(risk_category, allocations[RiskCategory.MODERATE])

    @staticmethod
    def get_risk_profile_description(risk_category: RiskCategory) -> Dict[str, any]:
        """
        Get detailed description and characteristics of risk profile

        Args:
            risk_category: RiskCategory enum

        Returns:
            Dictionary with profile description and characteristics
        """
        profiles = {
            RiskCategory.CONSERVATIVE: {
                "title": "Conservative Investor",
                "description": "You prioritize capital preservation and steady returns over high growth. You prefer stable, low-risk investments.",
                "characteristics": [
                    "Low tolerance for volatility",
                    "Priority on capital preservation",
                    "Prefer fixed income and stable returns",
                    "Comfortable with modest growth"
                ],
                "suitable_products": [
                    "Debt Mutual Funds",
                    "Fixed Deposits",
                    "Government Bonds",
                    "Large Cap Equity Funds (limited exposure)"
                ],
                "expected_return_range": "7-10% annually",
                "risk_level": "Low"
            },
            RiskCategory.MODERATE: {
                "title": "Moderate Investor",
                "description": "You seek a balanced approach with moderate growth and acceptable risk. You're comfortable with some market volatility.",
                "characteristics": [
                    "Balanced risk-return approach",
                    "Can tolerate moderate volatility",
                    "Mix of equity and debt",
                    "Long-term wealth creation focus"
                ],
                "suitable_products": [
                    "Balanced/Hybrid Funds",
                    "Large & Mid Cap Equity Funds",
                    "Debt Funds",
                    "Index Funds"
                ],
                "expected_return_range": "10-13% annually",
                "risk_level": "Medium"
            },
            RiskCategory.AGGRESSIVE: {
                "title": "Aggressive Investor",
                "description": "You aim for maximum growth and are willing to accept high volatility. You have a high risk tolerance and long investment horizon.",
                "characteristics": [
                    "High tolerance for volatility",
                    "Focus on wealth maximization",
                    "Long-term investment horizon",
                    "Can withstand short-term losses"
                ],
                "suitable_products": [
                    "Equity Mutual Funds (Mid/Small Cap)",
                    "Sectoral/Thematic Funds",
                    "Individual Stocks",
                    "ELSS Funds",
                    "Alternative Investments"
                ],
                "expected_return_range": "13-18% annually",
                "risk_level": "High"
            }
        }

        return profiles.get(risk_category, profiles[RiskCategory.MODERATE])

    @staticmethod
    def get_investment_strategy_recommendations(
        risk_category: RiskCategory,
        monthly_sip_capacity: Optional[float] = None,
        lumpsum_amount: Optional[float] = None
    ) -> Dict[str, any]:
        """
        Get personalized investment strategy recommendations

        Args:
            risk_category: RiskCategory enum
            monthly_sip_capacity: Monthly SIP amount available
            lumpsum_amount: Lumpsum investment amount

        Returns:
            Dictionary with strategy recommendations
        """
        strategy = {
            "risk_category": risk_category.value,
            "investment_approach": "",
            "recommended_vehicles": [],
            "rebalancing_frequency": "",
            "review_frequency": ""
        }

        if risk_category == RiskCategory.CONSERVATIVE:
            strategy["investment_approach"] = "Focus on capital preservation with steady income. Prioritize debt instruments with limited equity exposure."
            strategy["recommended_vehicles"] = [
                {"type": "Debt Funds", "allocation": "60-65%"},
                {"type": "Large Cap Equity", "allocation": "20-25%"},
                {"type": "Gold/Gold Funds", "allocation": "10%"},
                {"type": "Liquid Funds", "allocation": "5-10%"}
            ]
            strategy["rebalancing_frequency"] = "Annually"
            strategy["review_frequency"] = "Quarterly"

        elif risk_category == RiskCategory.MODERATE:
            strategy["investment_approach"] = "Balanced approach with diversified equity and debt. Focus on systematic wealth creation."
            strategy["recommended_vehicles"] = [
                {"type": "Large & Mid Cap Equity", "allocation": "40-45%"},
                {"type": "Debt Funds", "allocation": "30-35%"},
                {"type": "Hybrid Funds", "allocation": "10-15%"},
                {"type": "Gold/Gold Funds", "allocation": "10%"}
            ]
            strategy["rebalancing_frequency"] = "Half-yearly"
            strategy["review_frequency"] = "Quarterly"

        else:  # AGGRESSIVE
            strategy["investment_approach"] = "Maximize growth through high equity allocation. Leverage market opportunities with diversified equity portfolio."
            strategy["recommended_vehicles"] = [
                {"type": "Large Cap Equity", "allocation": "30-35%"},
                {"type": "Mid & Small Cap Equity", "allocation": "30-35%"},
                {"type": "Thematic/Sectoral Funds", "allocation": "10-15%"},
                {"type": "Debt Funds", "allocation": "10-15%"},
                {"type": "Gold/Gold Funds", "allocation": "10%"}
            ]
            strategy["rebalancing_frequency"] = "Quarterly"
            strategy["review_frequency"] = "Monthly"

        # Add SIP/Lumpsum recommendations
        if monthly_sip_capacity and lumpsum_amount:
            strategy["recommended_split"] = {
                "sip_percentage": 70,
                "lumpsum_percentage": 30,
                "rationale": "Combine SIP for rupee cost averaging with lumpsum for immediate market exposure"
            }
        elif monthly_sip_capacity:
            strategy["recommended_split"] = {
                "sip_percentage": 100,
                "lumpsum_percentage": 0,
                "rationale": "Systematic investment through SIP for rupee cost averaging and disciplined investing"
            }
        elif lumpsum_amount:
            strategy["recommended_split"] = {
                "sip_percentage": 0,
                "lumpsum_percentage": 100,
                "rationale": "Consider staggered lumpsum investment (STP) to reduce timing risk"
            }

        return strategy

    @staticmethod
    def validate_responses(responses: List[RiskProfileQuestionAnswer]) -> tuple[bool, Optional[str]]:
        """
        Validate questionnaire responses

        Args:
            responses: List of question-answer pairs

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not responses:
            return False, "No responses provided"

        if len(responses) != 10:
            return False, f"Expected 10 responses, got {len(responses)}"

        # Check all question IDs are present
        expected_ids = {f"Q{i}" for i in range(1, 11)}
        provided_ids = {r.question_id for r in responses}

        if expected_ids != provided_ids:
            missing = expected_ids - provided_ids
            extra = provided_ids - expected_ids
            error_parts = []
            if missing:
                error_parts.append(f"Missing: {', '.join(sorted(missing))}")
            if extra:
                error_parts.append(f"Extra: {', '.join(sorted(extra))}")
            return False, "; ".join(error_parts)

        # Validate score range for each response
        for response in responses:
            if not (1 <= response.score <= 4):
                return False, f"Invalid score {response.score} for {response.question_id}. Must be 1-4."

        return True, None
