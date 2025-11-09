"""
Goal-Based Planning Calculator Service
Handles financial goal calculations including SIP, lumpsum, and inflation adjustments
"""

import math
from typing import Dict, Optional, List
from datetime import datetime, timedelta


class GoalCalculatorService:
    """Service for financial goal calculations"""

    @staticmethod
    def calculate_inflation_adjusted_target(
        target_amount: float,
        years_to_goal: int,
        inflation_rate: float = 6.0
    ) -> float:
        """
        Calculate future value of goal considering inflation

        Formula: FV = PV × (1 + inflation_rate)^years

        Args:
            target_amount: Current value of the goal
            years_to_goal: Number of years until goal
            inflation_rate: Annual inflation rate (default 6% for India)

        Returns:
            Inflation-adjusted future value
        """
        if years_to_goal <= 0:
            return target_amount

        inflation_decimal = inflation_rate / 100
        future_value = target_amount * math.pow((1 + inflation_decimal), years_to_goal)

        return round(future_value, 2)

    @staticmethod
    def calculate_required_monthly_sip(
        target_amount: float,
        years_to_goal: int,
        expected_return: float = 12.0,
        current_savings: float = 0
    ) -> float:
        """
        Calculate required monthly SIP to achieve goal

        Formula: PMT = [FV × r] / [((1 + r)^n - 1) × (1 + r)]
        where:
        - FV = Future Value (target amount - future value of current savings)
        - r = Monthly return rate
        - n = Number of months

        Args:
            target_amount: Target amount to achieve
            years_to_goal: Number of years to achieve goal
            expected_return: Expected annual return rate (%)
            current_savings: Current savings towards goal

        Returns:
            Required monthly SIP amount
        """
        if years_to_goal <= 0:
            return target_amount - current_savings

        months = years_to_goal * 12
        monthly_return = (expected_return / 100) / 12

        # Calculate future value of current savings
        if current_savings > 0:
            fv_current_savings = current_savings * math.pow((1 + monthly_return), months)
        else:
            fv_current_savings = 0

        # Adjust target for current savings
        adjusted_target = target_amount - fv_current_savings

        if adjusted_target <= 0:
            return 0  # Current savings are sufficient

        # Calculate SIP using future value of annuity formula
        if monthly_return == 0:
            # If no returns, simple division
            sip_amount = adjusted_target / months
        else:
            # PMT = [FV × r] / [((1 + r)^n - 1) × (1 + r)]
            numerator = adjusted_target * monthly_return
            denominator = (math.pow((1 + monthly_return), months) - 1) * (1 + monthly_return)
            sip_amount = numerator / denominator

        return round(sip_amount, 2)

    @staticmethod
    def calculate_required_lumpsum(
        target_amount: float,
        years_to_goal: int,
        expected_return: float = 12.0,
        current_savings: float = 0
    ) -> float:
        """
        Calculate required one-time lumpsum investment to achieve goal

        Formula: PV = FV / (1 + r)^n

        Args:
            target_amount: Target amount to achieve
            years_to_goal: Number of years to achieve goal
            expected_return: Expected annual return rate (%)
            current_savings: Current savings towards goal

        Returns:
            Required lumpsum investment amount
        """
        if years_to_goal <= 0:
            return max(0, target_amount - current_savings)

        annual_return = expected_return / 100

        # Calculate present value needed
        present_value = target_amount / math.pow((1 + annual_return), years_to_goal)

        # Adjust for current savings
        required_lumpsum = present_value - current_savings

        return max(0, round(required_lumpsum, 2))

    @staticmethod
    def calculate_sip_future_value(
        monthly_sip: float,
        years: int,
        expected_return: float = 12.0,
        initial_investment: float = 0
    ) -> float:
        """
        Calculate future value of SIP investment

        Formula: FV = PMT × [((1 + r)^n - 1) × (1 + r)] / r + PV × (1 + r)^n

        Args:
            monthly_sip: Monthly SIP amount
            years: Investment tenure in years
            expected_return: Expected annual return rate (%)
            initial_investment: Initial lumpsum investment

        Returns:
            Future value of investment
        """
        months = years * 12
        monthly_return = (expected_return / 100) / 12

        if monthly_return == 0:
            # If no returns, simple sum
            sip_value = monthly_sip * months
        else:
            # FV of annuity due (SIP payments at beginning of month)
            sip_value = monthly_sip * (math.pow((1 + monthly_return), months) - 1) * (1 + monthly_return) / monthly_return

        # Add future value of initial investment
        if initial_investment > 0:
            annual_return = expected_return / 100
            lumpsum_value = initial_investment * math.pow((1 + annual_return), years)
        else:
            lumpsum_value = 0

        total_value = sip_value + lumpsum_value

        return round(total_value, 2)

    @staticmethod
    def calculate_lumpsum_future_value(
        lumpsum_amount: float,
        years: int,
        expected_return: float = 12.0
    ) -> float:
        """
        Calculate future value of lumpsum investment

        Formula: FV = PV × (1 + r)^n

        Args:
            lumpsum_amount: One-time investment amount
            years: Investment tenure in years
            expected_return: Expected annual return rate (%)

        Returns:
            Future value of lumpsum investment
        """
        annual_return = expected_return / 100
        future_value = lumpsum_amount * math.pow((1 + annual_return), years)

        return round(future_value, 2)

    @staticmethod
    def calculate_year_wise_projections(
        monthly_sip: float = 0,
        lumpsum_amount: float = 0,
        years: int = 10,
        expected_return: float = 12.0
    ) -> List[Dict]:
        """
        Calculate year-wise portfolio value projections

        Args:
            monthly_sip: Monthly SIP amount
            lumpsum_amount: Initial lumpsum investment
            years: Number of years to project
            expected_return: Expected annual return rate (%)

        Returns:
            List of year-wise projections with invested, returns, and total
        """
        projections = []
        monthly_return = (expected_return / 100) / 12
        annual_return = expected_return / 100

        for year in range(1, years + 1):
            months_elapsed = year * 12

            # Calculate SIP value
            if monthly_sip > 0 and monthly_return != 0:
                sip_value = monthly_sip * (math.pow((1 + monthly_return), months_elapsed) - 1) * (1 + monthly_return) / monthly_return
            else:
                sip_value = monthly_sip * months_elapsed

            # Calculate lumpsum value
            if lumpsum_amount > 0:
                lumpsum_value = lumpsum_amount * math.pow((1 + annual_return), year)
            else:
                lumpsum_value = 0

            total_value = sip_value + lumpsum_value
            total_invested = (monthly_sip * months_elapsed) + lumpsum_amount
            total_returns = total_value - total_invested

            projections.append({
                "year": year,
                "invested": round(total_invested, 2),
                "returns": round(total_returns, 2),
                "total_value": round(total_value, 2)
            })

        return projections

    @staticmethod
    def calculate_goal_feasibility(
        target_amount: float,
        years_to_goal: int,
        monthly_sip: float = 0,
        lumpsum_amount: float = 0,
        expected_return: float = 12.0,
        current_savings: float = 0
    ) -> Dict:
        """
        Analyze if a goal is achievable with given investment parameters

        Args:
            target_amount: Target amount to achieve
            years_to_goal: Number of years to achieve goal
            monthly_sip: Proposed monthly SIP
            lumpsum_amount: Proposed lumpsum investment
            expected_return: Expected annual return rate
            current_savings: Current savings towards goal

        Returns:
            Dictionary with feasibility analysis
        """
        # Calculate future value with proposed investments
        projected_value = GoalCalculatorService.calculate_sip_future_value(
            monthly_sip=monthly_sip,
            years=years_to_goal,
            expected_return=expected_return,
            initial_investment=lumpsum_amount + current_savings
        )

        # Calculate shortfall or surplus
        difference = projected_value - target_amount
        is_achievable = difference >= 0

        # Calculate required adjustments if not achievable
        if not is_achievable:
            required_sip = GoalCalculatorService.calculate_required_monthly_sip(
                target_amount=target_amount,
                years_to_goal=years_to_goal,
                expected_return=expected_return,
                current_savings=current_savings + lumpsum_amount
            )
            additional_sip_needed = max(0, required_sip - monthly_sip)
        else:
            additional_sip_needed = 0

        return {
            "is_achievable": is_achievable,
            "projected_value": round(projected_value, 2),
            "target_amount": round(target_amount, 2),
            "surplus_shortfall": round(difference, 2),
            "achievement_percentage": round((projected_value / target_amount) * 100, 2) if target_amount > 0 else 0,
            "additional_sip_needed": round(additional_sip_needed, 2),
            "confidence_level": "HIGH" if is_achievable and difference > (target_amount * 0.1) else
                               "MEDIUM" if is_achievable else
                               "LOW" if difference > -(target_amount * 0.2) else
                               "VERY LOW"
        }

    @staticmethod
    def calculate_retirement_corpus(
        current_age: int,
        retirement_age: int,
        monthly_expenses: float,
        expected_inflation: float = 6.0,
        life_expectancy: int = 85,
        post_retirement_return: float = 7.0
    ) -> Dict:
        """
        Calculate retirement corpus requirement

        Args:
            current_age: Current age
            retirement_age: Expected retirement age
            monthly_expenses: Current monthly expenses
            expected_inflation: Expected inflation rate (%)
            life_expectancy: Expected life expectancy
            post_retirement_return: Expected returns post-retirement (%)

        Returns:
            Dictionary with retirement calculations
        """
        years_to_retirement = retirement_age - current_age
        years_in_retirement = life_expectancy - retirement_age

        if years_to_retirement <= 0:
            years_to_retirement = 1

        if years_in_retirement <= 0:
            years_in_retirement = 20  # Default 20 years

        # Calculate inflation-adjusted monthly expenses at retirement
        annual_expenses = monthly_expenses * 12
        retirement_annual_expenses = GoalCalculatorService.calculate_inflation_adjusted_target(
            target_amount=annual_expenses,
            years_to_goal=years_to_retirement,
            inflation_rate=expected_inflation
        )

        # Calculate corpus needed to sustain retirement years
        # Using present value of annuity formula adjusted for inflation
        real_return = ((1 + post_retirement_return/100) / (1 + expected_inflation/100) - 1) * 100

        if real_return <= 0:
            # If real return is negative or zero, simple multiplication
            required_corpus = retirement_annual_expenses * years_in_retirement
        else:
            # PV of annuity formula
            r = real_return / 100
            n = years_in_retirement
            required_corpus = retirement_annual_expenses * ((1 - math.pow((1 + r), -n)) / r)

        return {
            "years_to_retirement": years_to_retirement,
            "years_in_retirement": years_in_retirement,
            "current_annual_expenses": round(annual_expenses, 2),
            "retirement_annual_expenses": round(retirement_annual_expenses, 2),
            "required_corpus": round(required_corpus, 2),
            "monthly_expenses_at_retirement": round(retirement_annual_expenses / 12, 2)
        }

    @staticmethod
    def calculate_education_goal(
        child_current_age: int,
        education_start_age: int,
        current_education_cost: float,
        education_inflation: float = 9.0,  # Higher than general inflation
        expected_return: float = 12.0,
        current_savings: float = 0
    ) -> Dict:
        """
        Calculate education goal planning

        Args:
            child_current_age: Child's current age
            education_start_age: Age when education starts (e.g., 18 for college)
            current_education_cost: Current cost of education
            education_inflation: Education-specific inflation rate (%)
            expected_return: Expected investment return (%)
            current_savings: Current savings for education

        Returns:
            Dictionary with education goal calculations
        """
        years_to_goal = education_start_age - child_current_age

        if years_to_goal <= 0:
            years_to_goal = 1

        # Calculate future cost of education
        future_cost = GoalCalculatorService.calculate_inflation_adjusted_target(
            target_amount=current_education_cost,
            years_to_goal=years_to_goal,
            inflation_rate=education_inflation
        )

        # Calculate required monthly SIP
        required_sip = GoalCalculatorService.calculate_required_monthly_sip(
            target_amount=future_cost,
            years_to_goal=years_to_goal,
            expected_return=expected_return,
            current_savings=current_savings
        )

        # Calculate required lumpsum (if starting today)
        required_lumpsum = GoalCalculatorService.calculate_required_lumpsum(
            target_amount=future_cost,
            years_to_goal=years_to_goal,
            expected_return=expected_return,
            current_savings=current_savings
        )

        return {
            "child_current_age": child_current_age,
            "education_start_age": education_start_age,
            "years_to_goal": years_to_goal,
            "current_cost": round(current_education_cost, 2),
            "future_cost": round(future_cost, 2),
            "current_savings": round(current_savings, 2),
            "required_monthly_sip": round(required_sip, 2),
            "required_lumpsum": round(required_lumpsum, 2),
            "inflation_impact": round(future_cost - current_education_cost, 2)
        }
