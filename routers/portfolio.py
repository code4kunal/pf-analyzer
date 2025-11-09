"""
Portfolio Construction API Endpoints
Generates data-driven model portfolios with tax harvesting and live MF data
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from models import User, ClientProfilingResponse, Prospect, RiskCategory
from schemas import (
    PortfolioGenerationRequest,
    ModelPortfolioResponse,
    PortfolioComparisonResponse
)
from services.portfolio_construction_service import PortfolioConstructionService
from services.mutual_fund_api_service import MutualFundAPIService
import auth

router = APIRouter(prefix="/api/portfolio", tags=["Portfolio Construction"])


@router.post("/generate", response_model=PortfolioComparisonResponse)
async def generate_portfolios(
    request: PortfolioGenerationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_user)
):
    """
    Generate 2-3 model portfolio options based on client profile

    Features:
    - Equity-focused strategy (70-80%)
    - Mutual funds as risk cushion
    - Tax harvesting (₹1.25L every 2 years)
    - SIP step-up projections
    - Portfolio health scoring
    """
    try:
        # Validate that at least one investment capacity is provided
        if request.monthly_sip == 0 and request.lumpsum == 0:
            raise HTTPException(
                status_code=400,
                detail="Please provide at least one: monthly SIP or lumpsum amount"
            )

        # Generate model portfolios
        portfolios = PortfolioConstructionService.generate_model_portfolios(
            risk_profile=request.risk_profile.value,
            monthly_sip=request.monthly_sip,
            lumpsum=request.lumpsum,
            timeline_years=request.timeline_years,
            step_up_percent=request.step_up_percent,
            equity_preference=request.equity_preference
        )

        # Add live mutual fund data to each portfolio
        for portfolio in portfolios:
            mf_breakdown = portfolio["allocation"]["mutual_funds"]["breakdown"]

            # Get recommended schemes
            schemes = MutualFundAPIService.get_portfolio_schemes(
                risk_profile=request.risk_profile.value,
                equity_breakdown={},
                mf_breakdown={
                    "debt": mf_breakdown["debt"]["percent"],
                    "hybrid": mf_breakdown["hybrid"]["percent"],
                    "gold": mf_breakdown["gold"]["percent"]
                }
            )

            portfolio["mutual_fund_schemes"] = schemes

            # Calculate health score
            health_score = PortfolioConstructionService.calculate_portfolio_health_score(portfolio)
            portfolio["health_score"] = health_score

        # Comparison metrics
        comparison_metrics = {
            "min_final_value": min(p["projections"]["final_value"] for p in portfolios),
            "max_final_value": max(p["projections"]["final_value"] for p in portfolios),
            "avg_cagr": sum(p["projections"]["cagr"] for p in portfolios) / len(portfolios),
            "total_tax_saved": sum(p["tax_harvesting"]["total_harvested"] for p in portfolios) / len(portfolios),
            "recommended_index": 0  # First portfolio is recommended
        }

        return {
            "portfolios": portfolios,
            "comparison_metrics": comparison_metrics
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating portfolios: {str(e)}")


@router.post("/from-response/{response_id}", response_model=PortfolioComparisonResponse)
async def generate_from_questionnaire(
    response_id: int,
    step_up_percent: float = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_user)
):
    """
    Generate portfolios directly from questionnaire response
    Auto-extracts risk profile, investment capacity, and timeline
    """
    try:
        # Get questionnaire response
        response = db.query(ClientProfilingResponse).filter(
            ClientProfilingResponse.id == response_id
        ).first()

        if not response:
            raise HTTPException(status_code=404, detail="Questionnaire response not found")

        # Extract parameters from response
        request = PortfolioGenerationRequest(
            response_id=response_id,
            risk_profile=response.calculated_risk_category,
            monthly_sip=response.monthly_investment_capacity or 0,
            lumpsum=response.lumpsum_availability or 0,
            timeline_years=10,  # Default, can be extracted from investment_timeline
            step_up_percent=step_up_percent
        )

        # Use the main generation endpoint
        return await generate_portfolios(request, db, current_user)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating from response: {str(e)}")


@router.get("/schemes/{category}")
async def get_mutual_fund_schemes(
    category: str,
    count: int = 3,
    use_live_data: bool = True,
    current_user: User = Depends(auth.get_current_user)
):
    """
    Get recommended mutual fund schemes by category

    Categories: large_cap, mid_cap, small_cap, debt, hybrid, gold
    """
    try:
        valid_categories = ["large_cap", "mid_cap", "small_cap", "debt", "hybrid", "gold"]

        if category not in valid_categories:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category. Must be one of: {', '.join(valid_categories)}"
            )

        schemes = MutualFundAPIService.get_recommended_schemes(
            category=category,
            count=count,
            use_live_data=use_live_data
        )

        return {
            "category": category,
            "count": len(schemes),
            "schemes": schemes
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching schemes: {str(e)}")


@router.get("/scheme/{scheme_code}")
async def get_scheme_details(
    scheme_code: str,
    current_user: User = Depends(auth.get_current_user)
):
    """Get detailed information about a specific mutual fund scheme"""
    try:
        details = MutualFundAPIService.get_scheme_details(scheme_code)

        if not details:
            raise HTTPException(status_code=404, detail="Scheme not found or API unavailable")

        return details

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching scheme details: {str(e)}")


@router.get("/search/{search_term}")
async def search_schemes(
    search_term: str,
    limit: int = 10,
    current_user: User = Depends(auth.get_current_user)
):
    """Search for mutual fund schemes by name or fund house"""
    try:
        if len(search_term) < 3:
            raise HTTPException(
                status_code=400,
                detail="Search term must be at least 3 characters"
            )

        results = MutualFundAPIService.search_schemes(search_term, limit)

        return {
            "search_term": search_term,
            "count": len(results),
            "results": results
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching schemes: {str(e)}")


@router.post("/health-score")
async def calculate_health_score(
    portfolio: dict,
    current_user: User = Depends(auth.get_current_user)
):
    """
    Calculate portfolio health score (0-100)

    Metrics:
    - Diversification (40 points)
    - Risk-adjusted returns (40 points)
    - Tax efficiency (20 points)
    """
    try:
        health_score = PortfolioConstructionService.calculate_portfolio_health_score(portfolio)

        return health_score

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating health score: {str(e)}")
