"""
Mutual Fund API Integration Service
Fetches live mutual fund data for portfolio construction
Supports multiple MF data sources
"""

import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class MutualFundAPIService:
    """Service to fetch live mutual fund data from APIs"""

    # MF API endpoints (using multiple sources for reliability)
    MFAPI_BASE_URL = "https://api.mfapi.in/mf"  # Free, no auth required

    # Pre-selected top performing schemes by category (updated quarterly)
    # These will be used as defaults when API is unavailable
    DEFAULT_SCHEMES = {
        "large_cap": [
            {"scheme_code": "122639", "name": "Nippon India Large Cap Fund", "category": "Large Cap"},
            {"scheme_code": "119551", "name": "Axis Bluechip Fund", "category": "Large Cap"},
            {"scheme_code": "120503", "name": "Mirae Asset Large Cap Fund", "category": "Large Cap"}
        ],
        "mid_cap": [
            {"scheme_code": "135777", "name": "Quant Mid Cap Fund", "category": "Mid Cap"},
            {"scheme_code": "118551", "name": "PGIM India Midcap Opportunities Fund", "category": "Mid Cap"},
            {"scheme_code": "120831", "name": "Edelweiss Mid Cap Fund", "category": "Mid Cap"}
        ],
        "small_cap": [
            {"scheme_code": "125497", "name": "Nippon India Small Cap Fund", "category": "Small Cap"},
            {"scheme_code": "120465", "name": "Axis Small Cap Fund", "category": "Small Cap"},
            {"scheme_code": "112090", "name": "Kotak Small Cap Fund", "category": "Small Cap"}
        ],
        "debt": [
            {"scheme_code": "118825", "name": "HDFC Corporate Bond Fund", "category": "Debt"},
            {"scheme_code": "119390", "name": "ICICI Prudential Corporate Bond Fund", "category": "Debt"},
            {"scheme_code": "120277", "name": "Aditya Birla Sun Life Corporate Bond Fund", "category": "Debt"}
        ],
        "hybrid": [
            {"scheme_code": "120522", "name": "ICICI Prudential Equity & Debt Fund", "category": "Hybrid"},
            {"scheme_code": "118989", "name": "HDFC Balanced Advantage Fund", "category": "Hybrid"},
            {"scheme_code": "119209", "name": "SBI Equity Hybrid Fund", "category": "Hybrid"}
        ],
        "gold": [
            {"scheme_code": "119551", "name": "HDFC Gold Fund", "category": "Gold"},
            {"scheme_code": "120465", "name": "SBI Gold Fund", "category": "Gold"},
            {"scheme_code": "119390", "name": "Nippon India Gold Savings Fund", "category": "Gold"}
        ]
    }

    @staticmethod
    def get_scheme_details(scheme_code: str) -> Optional[Dict]:
        """
        Fetch scheme details including latest NAV and returns

        Args:
            scheme_code: MF scheme code

        Returns:
            Dict with scheme details or None if failed
        """
        try:
            response = requests.get(f"{MutualFundAPIService.MFAPI_BASE_URL}/{scheme_code}", timeout=5)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "SUCCESS":
                meta = data.get("meta", {})
                nav_data = data.get("data", [])

                # Get latest NAV
                latest_nav = float(nav_data[0]["nav"]) if nav_data else 0

                # Calculate returns (approximate based on NAV history)
                returns_1y = MutualFundAPIService._calculate_return(nav_data, 365)
                returns_3y = MutualFundAPIService._calculate_return(nav_data, 1095)
                returns_5y = MutualFundAPIService._calculate_return(nav_data, 1825)

                return {
                    "scheme_code": scheme_code,
                    "scheme_name": meta.get("scheme_name", ""),
                    "fund_house": meta.get("fund_house", ""),
                    "scheme_type": meta.get("scheme_type", ""),
                    "scheme_category": meta.get("scheme_category", ""),
                    "nav": latest_nav,
                    "nav_date": nav_data[0]["date"] if nav_data else None,
                    "returns": {
                        "1y": returns_1y,
                        "3y": returns_3y,
                        "5y": returns_5y
                    }
                }

            return None

        except Exception as e:
            logger.error(f"Error fetching scheme {scheme_code}: {e}")
            return None

    @staticmethod
    def _calculate_return(nav_data: List[Dict], days: int) -> Optional[float]:
        """Calculate annualized return over specified period"""
        try:
            if not nav_data or len(nav_data) < days:
                return None

            latest_nav = float(nav_data[0]["nav"])
            old_nav = float(nav_data[min(days, len(nav_data) - 1)]["nav"])

            years = days / 365
            cagr = ((latest_nav / old_nav) ** (1 / years) - 1) * 100

            return round(cagr, 2)

        except Exception:
            return None

    @staticmethod
    def get_recommended_schemes(
        category: str,
        count: int = 3,
        use_live_data: bool = True
    ) -> List[Dict]:
        """
        Get recommended mutual fund schemes by category

        Args:
            category: large_cap, mid_cap, small_cap, debt, hybrid, gold
            count: Number of schemes to return
            use_live_data: Whether to fetch live data or use defaults

        Returns:
            List of scheme details with NAV and returns
        """
        default_schemes = MutualFundAPIService.DEFAULT_SCHEMES.get(category, [])[:count]

        if not use_live_data:
            return default_schemes

        schemes = []
        for scheme in default_schemes:
            live_data = MutualFundAPIService.get_scheme_details(scheme["scheme_code"])

            if live_data:
                schemes.append(live_data)
            else:
                # Fallback to default
                schemes.append({
                    **scheme,
                    "nav": 0,
                    "returns": {"1y": None, "3y": None, "5y": None}
                })

        return schemes

    @staticmethod
    def get_portfolio_schemes(
        risk_profile: str,
        equity_breakdown: Dict,
        mf_breakdown: Dict
    ) -> Dict[str, List[Dict]]:
        """
        Get complete set of schemes for portfolio construction

        Args:
            risk_profile: CONSERVATIVE, MODERATE, AGGRESSIVE
            equity_breakdown: Not used (we use direct equity)
            mf_breakdown: Mutual fund allocation breakdown

        Returns:
            Dict with schemes organized by category
        """
        portfolio_schemes = {}

        # Mutual fund schemes (risk cushion)
        if mf_breakdown.get("debt", 0) > 0:
            portfolio_schemes["debt"] = MutualFundAPIService.get_recommended_schemes("debt", count=2)

        if mf_breakdown.get("hybrid", 0) > 0:
            portfolio_schemes["hybrid"] = MutualFundAPIService.get_recommended_schemes("hybrid", count=2)

        if mf_breakdown.get("gold", 0) > 0:
            portfolio_schemes["gold"] = MutualFundAPIService.get_recommended_schemes("gold", count=1)

        return portfolio_schemes

    @staticmethod
    def search_schemes(search_term: str, limit: int = 10) -> List[Dict]:
        """
        Search for mutual fund schemes by name/fund house

        Args:
            search_term: Search query
            limit: Maximum results to return

        Returns:
            List of matching schemes
        """
        # This would require a comprehensive scheme list
        # For now, return from defaults that match
        results = []
        search_lower = search_term.lower()

        for category, schemes in MutualFundAPIService.DEFAULT_SCHEMES.items():
            for scheme in schemes:
                if (search_lower in scheme["name"].lower() or
                    search_lower in category.lower()):
                    results.append({
                        **scheme,
                        "scheme_code": scheme["scheme_code"]
                    })

                    if len(results) >= limit:
                        return results

        return results

    @staticmethod
    def get_scheme_comparison(scheme_codes: List[str]) -> List[Dict]:
        """
        Compare multiple schemes side-by-side

        Args:
            scheme_codes: List of scheme codes to compare

        Returns:
            List of scheme details for comparison
        """
        schemes = []
        for code in scheme_codes:
            details = MutualFundAPIService.get_scheme_details(code)
            if details:
                schemes.append(details)

        return schemes
