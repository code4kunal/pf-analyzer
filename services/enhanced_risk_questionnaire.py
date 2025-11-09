"""
Enhanced Risk Profiling Questionnaire with Detailed Explanations
Includes educational content about risk, drawdowns, and investment concepts
"""

# Complete Enhanced Questionnaire with Explanations
ENHANCED_QUESTIONNAIRE = [
    {
        "question_id": "Q1",
        "question_text": "What is your age group?",
        "section": "Personal Profile",
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
        "section": "Investment Goals",
        "explanation": "Your time horizon is when you expect to need the invested money. Longer horizons allow for higher equity exposure as you can wait out market downturns.",
        "help_text": "Time horizon directly impacts which assets are suitable for you. Equity investments need at least 5-7 years to deliver optimal returns.",
        "options": [
            {
                "answer": "More than 10 years",
                "score": 4,
                "description": "Long-term wealth creation - Can invest heavily in equity (70-80%) with expected returns of 12-15% p.a."
            },
            {
                "answer": "5-10 years",
                "score": 3,
                "description": "Medium-term goals - Balanced allocation (50-60% equity) targeting 10-12% returns"
            },
            {
                "answer": "3-5 years",
                "score": 2,
                "description": "Short-to-medium term - Conservative allocation (30-40% equity) for 8-10% returns"
            },
            {
                "answer": "Less than 3 years",
                "score": 1,
                "description": "Short-term preservation - Primarily debt (80%+) for stable 6-8% returns"
            }
        ]
    },
    {
        "question_id": "Q3",
        "question_text": "What percentage of your monthly income can you invest?",
        "section": "Investment Capacity",
        "explanation": "Higher savings rate indicates financial stability and ability to continue investing during market downturns, allowing for higher risk tolerance.",
        "help_text": "We recommend following the 50-30-20 rule: 50% needs, 30% wants, 20% savings. Investing 20%+ is considered healthy.",
        "options": [
            {
                "answer": "More than 30%",
                "score": 4,
                "description": "Excellent savings discipline - ₹30,000 monthly SIP on ₹1L income can grow to ₹3.5 Cr in 20 years @ 12%"
            },
            {
                "answer": "20-30%",
                "score": 3,
                "description": "Good savings rate - ₹25,000 SIP on ₹1L income → ₹2.9 Cr in 20 years @ 12%"
            },
            {
                "answer": "10-20%",
                "score": 2,
                "description": "Moderate savings - ₹15,000 SIP on ₹1L income → ₹1.7 Cr in 20 years @ 12%"
            },
            {
                "answer": "Less than 10%",
                "score": 1,
                "description": "Limited capacity - Focus on building emergency fund first, then increase SIP gradually"
            }
        ]
    },
    {
        "question_id": "Q4",
        "question_text": "How would you describe your knowledge of investments?",
        "section": "Investment Experience",
        "explanation": "Understanding investment concepts helps you stay calm during market volatility. Experienced investors can better assess and handle risk.",
        "help_text": "No worries if you're new! We'll guide you through every step. Knowledge can be built over time.",
        "options": [
            {
                "answer": "Excellent - I actively manage my portfolio",
                "score": 4,
                "description": "Experienced investor - Comfortable with equity volatility, understand P/E ratios, fund categories, and rebalancing"
            },
            {
                "answer": "Good - I understand stocks, bonds, and mutual funds",
                "score": 3,
                "description": "Knowledgeable investor - Know the difference between equity, debt, and hybrid funds"
            },
            {
                "answer": "Limited - I understand basic concepts",
                "score": 2,
                "description": "Learning investor - Know about mutual funds and SIPs, but need guidance on selection"
            },
            {
                "answer": "None - I'm new to investing",
                "score": 1,
                "description": "First-time investor - We'll start with simple, low-risk products and educate you along the way"
            }
        ]
    },
    {
        "question_id": "Q5",
        "question_text": "What is your primary investment objective?",
        "section": "Investment Goals",
        "explanation": "Your investment objective determines the right balance between growth and stability. Different goals require different strategies.",
        "help_text": "Be honest about your goals - this helps us create the right portfolio mix for you.",
        "options": [
            {
                "answer": "Aggressive growth - maximize returns",
                "score": 4,
                "description": "Target: 15-18% returns | Risk: Can face 30-40% drawdowns in bad years | Example: Mid/Small cap funds"
            },
            {
                "answer": "Growth - higher returns with moderate risk",
                "score": 3,
                "description": "Target: 12-15% returns | Risk: 20-25% drawdowns possible | Example: Large & Mid cap balanced portfolios"
            },
            {
                "answer": "Balanced - stable returns with some risk",
                "score": 2,
                "description": "Target: 9-12% returns | Risk: 10-15% drawdowns | Example: Hybrid funds with 60-70% debt"
            },
            {
                "answer": "Capital preservation - minimize risk",
                "score": 1,
                "description": "Target: 6-8% returns | Risk: Minimal drawdowns (2-5%) | Example: Debt funds, Fixed Deposits"
            }
        ]
    },
    {
        "question_id": "Q6",
        "question_text": "If your portfolio value dropped by 20% in a year, you would:",
        "section": "Risk Tolerance",
        "explanation": "DRAWDOWN EXPLAINED: A 20% fall means ₹10 lakhs becomes ₹8 lakhs temporarily. This is normal in equity investing. Markets recovered from COVID-19 crash (40% down) in just 6 months.",
        "help_text": "Historical context: Nifty50 fell 38% in 2008, but delivered 95% returns in next 2 years. Those who stayed invested benefited most.",
        "examples": [
            "2020 COVID Crash: -40% (March) → Recovered by August",
            "2008 Financial Crisis: -60% → Took 2 years to recover",
            "Since 2000: Nifty has had 6 corrections >20%, all recovered"
        ],
        "options": [
            {
                "answer": "Invest more - it's a buying opportunity",
                "score": 4,
                "description": "Aggressive investor - You understand 'buy the dip' strategy. Warren Buffett: 'Be fearful when others are greedy, greedy when others are fearful'"
            },
            {
                "answer": "Hold on - markets will recover",
                "score": 3,
                "description": "Patient investor - You trust the long-term growth story. Historical data shows markets always recover given sufficient time"
            },
            {
                "answer": "Worry but wait - give it some time",
                "score": 2,
                "description": "Cautious investor - Some anxiety is normal, but you need more debt allocation for peace of mind"
            },
            {
                "answer": "Sell immediately - I can't bear losses",
                "score": 1,
                "description": "Risk-averse investor - High equity allocation will cause stress. Debt funds (2-5% drawdown) are better suited"
            }
        ]
    },
    {
        "question_id": "Q7",
        "question_text": "What level of fluctuation in returns can you tolerate?",
        "section": "Risk Tolerance",
        "explanation": "VOLATILITY EXPLAINED: Investments fluctuate. Higher potential returns come with higher fluctuations. Understanding this helps set right expectations.",
        "help_text": "Risk vs Return Examples (based on historical data):",
        "risk_return_matrix": [
            {"portfolio": "100% Equity (Small Cap)", "best_year": "+85%", "worst_year": "-55%", "avg_return": "18%", "volatility": "Very High"},
            {"portfolio": "70% Equity + 30% Debt", "best_year": "+45%", "worst_year": "-25%", "avg_return": "13%", "volatility": "Moderate"},
            {"portfolio": "30% Equity + 70% Debt", "best_year": "+22%", "worst_year": "-8%", "avg_return": "9%", "volatility": "Low"},
            {"portfolio": "100% Debt Funds", "best_year": "+12%", "worst_year": "-2%", "avg_return": "7%", "volatility": "Very Low"}
        ],
        "options": [
            {
                "answer": "High fluctuation for potentially higher returns",
                "score": 4,
                "description": "Can accept -30% to -40% drawdowns | Expecting 15-18% long-term returns | Suitable: Small/Mid cap funds"
            },
            {
                "answer": "Moderate fluctuation for moderate returns",
                "score": 3,
                "description": "Comfortable with -15% to -20% drawdowns | Expecting 12-14% returns | Suitable: Large cap & balanced funds"
            },
            {
                "answer": "Low fluctuation for stable returns",
                "score": 2,
                "description": "Prefer -5% to -10% drawdowns | Expecting 9-11% returns | Suitable: Conservative hybrid funds"
            },
            {
                "answer": "No fluctuation - I want guaranteed returns",
                "score": 1,
                "description": "Cannot accept >5% drawdowns | Expecting 6-8% returns | Suitable: Debt funds, FDs, bonds"
            }
        ]
    },
    {
        "question_id": "Q8",
        "question_text": "Do you have any existing liabilities (loans, EMIs)?",
        "section": "Financial Stability",
        "explanation": "High liabilities reduce your ability to continue investing during emergencies or market downturns. Lower debt means more flexibility for aggressive investments.",
        "help_text": "THUMB RULE: EMI should not exceed 40% of monthly income. If it does, focus on debt reduction before aggressive investing.",
        "options": [
            {
                "answer": "No liabilities",
                "score": 4,
                "description": "Excellent position - Full flexibility to invest aggressively and hold during market downturns"
            },
            {
                "answer": "Minimal liabilities (< 20% of income)",
                "score": 3,
                "description": "Good position - EMI ₹20K on ₹1L income. Manageable, allows for growth investing"
            },
            {
                "answer": "Moderate liabilities (20-40% of income)",
                "score": 2,
                "description": "Cautious approach needed - EMI ₹30K on ₹1L income. Consider balanced portfolio"
            },
            {
                "answer": "High liabilities (> 40% of income)",
                "score": 1,
                "description": "Debt reduction priority - Focus on emergency fund and conservative investments first"
            }
        ]
    },
    {
        "question_id": "Q9",
        "question_text": "How stable is your current income source?",
        "section": "Financial Stability",
        "explanation": "Stable income allows you to continue SIPs during market crashes (best time to accumulate). Unstable income requires more liquid, low-risk investments.",
        "help_text": "SIP TIP: Most wealth is created by those who continue SIPs during market crashes. Stable income enables this discipline.",
        "options": [
            {
                "answer": "Very stable - salaried with job security",
                "score": 4,
                "description": "Ideal for SIP investing - Can continue ₹25K SIP even if markets fall 30%. This builds maximum wealth"
            },
            {
                "answer": "Stable - salaried but some uncertainty",
                "score": 3,
                "description": "Good for SIP with emergency fund - Keep 6-month expenses liquid, invest rest systematically"
            },
            {
                "answer": "Moderately stable - business/self-employed",
                "score": 2,
                "description": "Variable income strategy - Invest surplus in tranches, maintain larger emergency fund (12 months)"
            },
            {
                "answer": "Unstable - irregular income",
                "score": 1,
                "description": "Flexibility needed - Focus on liquid funds, debt funds. Avoid locking money long-term"
            }
        ]
    },
    {
        "question_id": "Q10",
        "question_text": "Do you have an emergency fund (6 months expenses)?",
        "section": "Financial Stability",
        "explanation": "EMERGENCY FUND: Essential safety net covering 6-12 months of expenses in liquid investments. Prevents forced selling of equity during emergencies or market lows.",
        "help_text": "CRITICAL: Without emergency fund, you may be forced to sell equity investments at a loss during personal emergencies or market crashes.",
        "importance": "An emergency fund is your financial foundation. It should be in liquid funds or savings account, not equity.",
        "calculation_help": "Monthly expenses ₹50K → Emergency fund needed: ₹3L (6 months) to ₹6L (12 months)",
        "options": [
            {
                "answer": "Yes, more than 12 months",
                "score": 4,
                "description": "Excellent safety net - You can invest 80-90% in growth assets without worry. Never need to sell during market lows"
            },
            {
                "answer": "Yes, 6-12 months",
                "score": 3,
                "description": "Good safety net - Adequate cushion for most emergencies. Can comfortably invest 60-70% in equity"
            },
            {
                "answer": "Partial - 3-6 months",
                "score": 2,
                "description": "Build it first - Complete your emergency fund before aggressive equity investing. Consider 50% equity allocation"
            },
            {
                "answer": "No emergency fund",
                "score": 1,
                "description": "PRIORITY: Build 6-month emergency fund FIRST in liquid/debt funds. Then start equity investments"
            }
        ]
    }
]

# Risk Category Detailed Explanations
RISK_CATEGORIES_DETAILED = {
    "CONSERVATIVE": {
        "title": "Conservative / Low-Risk Investor",
        "score_range": "10-18 points",
        "description": "You prioritize capital preservation and steady income over high growth. You prefer stable, predictable returns even if they're modest.",
        "drawdown_tolerance": "Maximum comfortable drawdown: 5-10%",
        "drawdown_explanation": "If you invest ₹10 lakhs, you're comfortable if it temporarily drops to ₹9-9.5 lakhs but not further. This aligns with debt/conservative hybrid funds.",
        "real_world_examples": [
            "2020 COVID crash: Conservative portfolios fell only 5-8% vs 40% for pure equity",
            "2008 crisis: Conservative portfolios fell 10-12% and recovered in 6 months",
            "2013 taper tantrum: Minimal impact, less than 5% decline"
        ],
        "asset_allocation": {
            "equity": "20-30%",
            "debt": "60-70%",
            "gold": "10%",
            "rationale": "Heavy debt allocation ensures stability. Limited equity exposure (20-30%) for some growth while keeping volatility low."
        },
        "recommended_products": [
            {
                "name": "Debt Mutual Funds",
                "allocation": "60-65%",
                "expected_return": "6-8% p.a.",
                "risk": "Very Low",
                "example": "HDFC Corporate Bond Fund - consistent 7% returns, maximum 2% drawdown historically"
            },
            {
                "name": "Conservative Hybrid Funds",
                "allocation": "15-20%",
                "expected_return": "8-10% p.a.",
                "risk": "Low",
                "example": "ICICI Pru Regular Savings Fund - 75% debt, 25% equity, smooth returns"
            },
            {
                "name": "Large Cap Equity Funds",
                "allocation": "10-15%",
                "expected_return": "10-12% p.a.",
                "risk": "Low-Moderate",
                "example": "Limited exposure to quality large caps for some growth"
            },
            {
                "name": "Gold/Gold ETF",
                "allocation": "10%",
                "expected_return": "6-8% p.a.",
                "risk": "Low",
                "example": "Acts as hedge against inflation and market volatility"
            }
        ],
        "expected_returns": {
            "best_year": "+15%",
            "worst_year": "-5%",
            "average_annual": "7-9%",
            "10_year_projection": "₹10L invested → ₹19-22L (conservative estimates)"
        },
        "suitable_for": [
            "Investors nearing retirement (55+ years)",
            "Very low risk tolerance",
            "Short investment horizon (< 5 years)",
            "Need for regular income",
            "First-time investors who want to start safely"
        ],
        "strategy_tips": [
            "Focus on capital preservation first, growth second",
            "Invest in high-quality debt funds with AAA-rated instruments",
            "Review portfolio quarterly",
            "Rebalance only when equity allocation exceeds 35%",
            "Keep 3-6 month expenses in liquid funds"
        ]
    },
    "MODERATE": {
        "title": "Moderate / Balanced Investor",
        "score_range": "19-28 points",
        "description": "You seek balanced growth with acceptable levels of risk. You can tolerate moderate market fluctuations for better long-term returns.",
        "drawdown_tolerance": "Maximum comfortable drawdown: 15-20%",
        "drawdown_explanation": "If you invest ₹10 lakhs, you can handle it dropping to ₹8-8.5 lakhs temporarily, knowing it will likely recover and grow. This is typical for balanced portfolios.",
        "real_world_examples": [
            "2020 COVID crash: Balanced portfolios fell 15-20%, fully recovered in 5-6 months",
            "2008 crisis: Fell 25-30%, took 18 months to recover but then grew strongly",
            "2011-2013 correction: Moderate impact, 12-15% decline, recovered in 12 months"
        ],
        "asset_allocation": {
            "equity": "50-60%",
            "debt": "30-40%",
            "gold": "10%",
            "rationale": "Balanced mix provides growth potential from equity while debt cushions market falls. Historically optimal for 5-10 year goals."
        },
        "recommended_products": [
            {
                "name": "Large & Mid Cap Equity Funds",
                "allocation": "35-40%",
                "expected_return": "12-14% p.a.",
                "risk": "Moderate",
                "example": "Parag Parikh Flexi Cap Fund - diversified across market caps, 25-year track record"
            },
            {
                "name": "Balanced Hybrid Funds",
                "allocation": "15-20%",
                "expected_return": "10-12% p.a.",
                "risk": "Moderate",
                "example": "HDFC Balanced Advantage Fund - dynamic allocation based on valuations"
            },
            {
                "name": "Corporate Bond Funds",
                "allocation": "25-30%",
                "expected_return": "7-8% p.a.",
                "risk": "Low",
                "example": "Provides stability during equity corrections"
            },
            {
                "name": "Gold ETF",
                "allocation": "10%",
                "expected_return": "6-8% p.a.",
                "risk": "Low",
                "example": "Portfolio diversifier, negative correlation with equity"
            }
        ],
        "expected_returns": {
            "best_year": "+30%",
            "worst_year": "-15%",
            "average_annual": "10-13%",
            "10_year_projection": "₹10L invested → ₹26-35L",
            "sip_example": "₹25K monthly SIP for 20 years @ 12% = ₹2.5 Crore"
        },
        "suitable_for": [
            "Age 35-55 years with 10-20 year horizon",
            "Medium risk tolerance",
            "Goals like retirement planning, child's education",
            "Investors who want growth but can't handle extreme volatility",
            "Those with stable income and emergency fund in place"
        ],
        "strategy_tips": [
            "Continue SIP even during market falls - this is when you accumulate more units",
            "Rebalance twice a year when allocation drifts >5%",
            "In market crashes, consider increasing equity allocation",
            "Review portfolio half-yearly",
            "Step up SIP by 10% annually as income grows"
        ]
    },
    "AGGRESSIVE": {
        "title": "Aggressive / High-Risk Investor",
        "score_range": "29-40 points",
        "description": "You aim for maximum wealth creation and are willing to accept significant short-term volatility for superior long-term returns.",
        "drawdown_tolerance": "Maximum comfortable drawdown: 30-40%",
        "drawdown_explanation": "If you invest ₹10 lakhs, you can stomach it dropping to ₹6-7 lakhs during severe market crashes. You understand this is temporary and part of equity investing. Historical data shows such crashes recover and deliver superior returns to those who stay invested.",
        "real_world_examples": [
            "2020 COVID crash: Aggressive portfolios fell 35-40%, but those who held made 80%+ returns in next 12 months",
            "2008 crisis: Fell 50-60%, took 2 years to recover, but delivered 120%+ returns to those who continued SIPs",
            "1992-2000: Sensex delivered 18% CAGR despite multiple corrections",
            "Small cap funds: In 2017, some funds fell 30% but delivered 45%+ in 2020-21"
        ],
        "asset_allocation": {
            "equity": "70-80%",
            "debt": "10-20%",
            "gold": "10%",
            "rationale": "Heavy equity allocation for maximum growth. Small debt allocation provides liquidity during emergencies without selling equity at loss."
        },
        "recommended_products": [
            {
                "name": "Large Cap Equity Funds",
                "allocation": "30-35%",
                "expected_return": "12-15% p.a.",
                "risk": "Moderate-High",
                "example": "Mirae Asset Large Cap Fund - core holding, quality stocks, lower volatility"
            },
            {
                "name": "Mid & Small Cap Equity Funds",
                "allocation": "30-35%",
                "expected_return": "15-18% p.a.",
                "risk": "Very High",
                "example": "Axis Small Cap Fund, Kotak Emerging Equity - high growth potential, high volatility"
            },
            {
                "name": "Sectoral/Thematic Funds",
                "allocation": "10-15%",
                "expected_return": "18-25% p.a. (cyclical)",
                "risk": "Extremely High",
                "example": "Technology, Infrastructure, Banking funds - timing dependent, can give exceptional returns"
            },
            {
                "name": "Debt/Liquid Funds",
                "allocation": "10-15%",
                "expected_return": "6-7% p.a.",
                "risk": "Very Low",
                "example": "Emergency fund and tactical allocation for market opportunities"
            },
            {
                "name": "Gold ETF",
                "allocation": "5-10%",
                "expected_return": "6-8% p.a.",
                "risk": "Low",
                "example": "Portfolio stabilizer during extreme equity corrections"
            }
        ],
        "expected_returns": {
            "best_year": "+60% to +80%",
            "worst_year": "-35% to -45%",
            "average_annual": "14-18%",
            "10_year_projection": "₹10L invested → ₹37-50L",
            "sip_example": "₹25K monthly SIP for 20 years @ 15% = ₹3.8 Crore (vs ₹2.5Cr at 12%)"
        },
        "suitable_for": [
            "Age below 40 with 15+ year horizon",
            "High risk tolerance and market knowledge",
            "Stable, high income with strong emergency fund",
            "No near-term liquidity needs",
            "Investors who won't panic sell during crashes",
            "Those who understand and accept volatility"
        ],
        "strategy_tips": [
            "CRITICAL: Never stop SIP during market crashes - maximum wealth is created here",
            "In 30%+ corrections, deploy lumpsum if available (buy the dip)",
            "Maintain at least 12-month emergency fund - never sell equity for emergencies",
            "Review portfolio quarterly but don't react to short-term movements",
            "Rebalance only when equity exceeds 85% or falls below 65%",
            "Consider profit booking only after exceptional years (>30% returns)",
            "Study market history - every crash has recovered, no exception"
        ],
        "important_warnings": [
            "Not suitable if you need money within 5 years",
            "You must have 12-month emergency fund in liquid investments",
            "Requires emotional discipline to not panic sell",
            "Short-term performance can be very volatile",
            "Expect 2-3 major corrections (20%+) in every 10-year period"
        ]
    }
}
