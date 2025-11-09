"""
Client Profiling Questionnaire Service
Handles invite creation, token management, and response processing
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from models import (
    QuestionnaireInvite, ClientProfilingResponse, Prospect,
    QuestionnaireInviteStatus, ProspectStatus, ProspectPriority, ProspectSource,
    RiskCategory
)
from schemas import (
    QuestionnaireInviteCreate, ClientProfilingSubmission,
    RiskProfileQuestionAnswer
)
from services.risk_profiling_service import RiskProfilingService
import logging

logger = logging.getLogger(__name__)


class QuestionnaireService:
    """Service for client profiling questionnaire operations"""

    @staticmethod
    def generate_unique_token(db: Session, length: int = 32) -> str:
        """
        Generate a cryptographically secure unique token

        Args:
            db: Database session
            length: Token length in characters

        Returns:
            Unique token string
        """
        while True:
            token = secrets.token_urlsafe(length)
            # Ensure uniqueness
            existing = db.query(QuestionnaireInvite).filter(
                QuestionnaireInvite.invite_token == token
            ).first()
            if not existing:
                return token

    @staticmethod
    def create_invite(
        db: Session,
        invite_data: QuestionnaireInviteCreate,
        created_by_id: int,
        base_url: str = "https://yourdomain.com"
    ) -> QuestionnaireInvite:
        """
        Create a new questionnaire invite

        Args:
            db: Database session
            invite_data: Invite creation data
            created_by_id: User ID creating the invite
            base_url: Base URL for generating invite link

        Returns:
            Created QuestionnaireInvite object
        """
        # Generate unique token
        token = QuestionnaireService.generate_unique_token(db)

        # Calculate expiry date
        expires_at = None
        if invite_data.expires_in_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=invite_data.expires_in_days)

        # Create invite
        invite = QuestionnaireInvite(
            invite_token=token,
            recipient_name=invite_data.recipient_name,
            recipient_email=invite_data.recipient_email,
            recipient_phone=invite_data.recipient_phone,
            created_by_id=created_by_id,
            expires_at=expires_at,
            auto_create_prospect=invite_data.auto_create_prospect,
            notes=invite_data.notes,
            custom_message=invite_data.custom_message
        )

        db.add(invite)
        db.commit()
        db.refresh(invite)

        logger.info(f"Created questionnaire invite {invite.id} for {invite.recipient_email}")

        return invite

    @staticmethod
    def get_invite_by_token(db: Session, token: str) -> Optional[QuestionnaireInvite]:
        """
        Get invite by token

        Args:
            db: Database session
            token: Invite token

        Returns:
            QuestionnaireInvite or None
        """
        return db.query(QuestionnaireInvite).filter(
            QuestionnaireInvite.invite_token == token
        ).first()

    @staticmethod
    def is_invite_valid(invite: QuestionnaireInvite) -> tuple[bool, Optional[str]]:
        """
        Check if invite is valid for submission

        Args:
            invite: QuestionnaireInvite object

        Returns:
            Tuple of (is_valid, error_message)
        """
        if invite.status == QuestionnaireInviteStatus.COMPLETED:
            return False, "This questionnaire has already been completed"

        if invite.expires_at and datetime.now(timezone.utc) > invite.expires_at:
            return False, "This invite link has expired"

        return True, None

    @staticmethod
    def submit_questionnaire(
        db: Session,
        token: str,
        submission: ClientProfilingSubmission
    ) -> Dict:
        """
        Process questionnaire submission

        Args:
            db: Database session
            token: Invite token
            submission: Complete questionnaire submission

        Returns:
            Dictionary with submission result
        """
        # Get invite
        invite = QuestionnaireService.get_invite_by_token(db, token)
        if not invite:
            raise ValueError("Invalid invite token")

        # Validate invite
        is_valid, error_msg = QuestionnaireService.is_invite_valid(invite)
        if not is_valid:
            raise ValueError(error_msg)

        # Validate risk questionnaire responses
        is_valid_risk, risk_error = RiskProfilingService.validate_responses(
            submission.risk_questionnaire_responses
        )
        if not is_valid_risk:
            raise ValueError(f"Invalid risk questionnaire responses: {risk_error}")

        # Calculate risk score and category
        risk_score = RiskProfilingService.calculate_risk_score(
            submission.risk_questionnaire_responses
        )
        risk_category = RiskProfilingService.determine_risk_category(risk_score)

        # Create client profiling response
        response = ClientProfilingResponse(
            invite_id=invite.id,
            full_name=submission.full_name,
            email=submission.email,
            phone=submission.phone,
            date_of_birth=submission.date_of_birth,
            occupation=submission.occupation,
            annual_income=submission.annual_income,
            monthly_income=submission.monthly_income,
            monthly_expenses=submission.monthly_expenses,
            existing_investments=submission.existing_investments,
            existing_liabilities=submission.existing_liabilities,
            emergency_fund_months=submission.emergency_fund_months,
            investment_experience=submission.investment_experience,
            preferred_investment_types=submission.preferred_investment_types,
            investment_timeline=submission.investment_timeline,
            monthly_investment_capacity=submission.monthly_investment_capacity,
            lumpsum_availability=submission.lumpsum_availability,
            financial_goals=[goal.dict() for goal in submission.financial_goals],
            risk_questionnaire_responses=[resp.dict() for resp in submission.risk_questionnaire_responses],
            calculated_risk_score=risk_score,
            calculated_risk_category=risk_category,
            current_advisor=submission.current_advisor,
            how_did_you_hear=submission.how_did_you_hear,
            specific_requirements=submission.specific_requirements,
            preferred_contact_time=submission.preferred_contact_time
        )

        db.add(response)

        # Auto-create prospect if enabled
        prospect = None
        if invite.auto_create_prospect:
            prospect = QuestionnaireService._create_prospect_from_response(
                db=db,
                response=response,
                created_by_id=invite.created_by_id
            )
            response.prospect_id = prospect.id
            invite.created_prospect_id = prospect.id

        # Update invite status
        invite.status = QuestionnaireInviteStatus.COMPLETED
        invite.completed_at = datetime.now(timezone.utc)
        invite.response_data = submission.dict()

        db.commit()
        db.refresh(response)

        logger.info(f"Questionnaire submitted successfully for invite {invite.id}")
        if prospect:
            logger.info(f"Auto-created prospect {prospect.id} from questionnaire")

        return {
            "success": True,
            "response_id": response.id,
            "prospect_id": prospect.id if prospect else None,
            "risk_category": risk_category.value,
            "risk_score": risk_score,
            "message": "Thank you for completing the questionnaire! Our team will reach out to you soon."
        }

    @staticmethod
    def _create_prospect_from_response(
        db: Session,
        response: ClientProfilingResponse,
        created_by_id: int
    ) -> Prospect:
        """
        Create a prospect from questionnaire response

        Args:
            db: Database session
            response: ClientProfilingResponse object
            created_by_id: User ID creating the prospect

        Returns:
            Created Prospect object
        """
        # Determine priority based on investment capacity and risk category
        priority = ProspectPriority.WARM  # Default
        if response.monthly_investment_capacity and response.monthly_investment_capacity > 50000:
            priority = ProspectPriority.HOT
        elif response.lumpsum_availability and response.lumpsum_availability > 500000:
            priority = ProspectPriority.HOT

        # Build notes from questionnaire data
        notes_parts = []

        if response.investment_experience:
            notes_parts.append(f"Investment Experience: {response.investment_experience}")

        if response.financial_goals:
            goal_summary = ", ".join([g.get('goal_name', g.get('goal_type')) for g in response.financial_goals[:3]])
            notes_parts.append(f"Goals: {goal_summary}")

        if response.calculated_risk_category:
            notes_parts.append(f"Risk Profile: {response.calculated_risk_category.value}")

        if response.specific_requirements:
            notes_parts.append(f"Requirements: {response.specific_requirements}")

        notes = "\n".join(notes_parts)

        # Create prospect
        prospect = Prospect(
            full_name=response.full_name,
            email=response.email,
            phone=response.phone,
            status=ProspectStatus.NEW,
            priority=priority,
            source=ProspectSource.WEBSITE,  # Since it came from online form
            estimated_portfolio_value=response.existing_investments,
            notes=notes,
            created_by_id=created_by_id,
            import_file_name="Client Profiling Questionnaire"
        )

        db.add(prospect)
        db.flush()  # Get prospect ID without committing

        return prospect

    @staticmethod
    def get_analytics(db: Session, created_by_id: Optional[int] = None) -> Dict:
        """
        Get analytics for questionnaire invites

        Args:
            db: Database session
            created_by_id: Optional filter by creator

        Returns:
            Dictionary with analytics data
        """
        # Base query
        query = db.query(QuestionnaireInvite)
        if created_by_id:
            query = query.filter(QuestionnaireInvite.created_by_id == created_by_id)

        # Total counts
        total_invites = query.count()
        pending = query.filter(QuestionnaireInvite.status == QuestionnaireInviteStatus.PENDING).count()
        completed = query.filter(QuestionnaireInvite.status == QuestionnaireInviteStatus.COMPLETED).count()

        # Expired invites
        now = datetime.now(timezone.utc)
        expired = query.filter(
            and_(
                QuestionnaireInvite.expires_at != None,
                QuestionnaireInvite.expires_at < now,
                QuestionnaireInvite.status == QuestionnaireInviteStatus.PENDING
            )
        ).count()

        completion_rate = (completed / total_invites * 100) if total_invites > 0 else 0

        # Get completed responses for deeper analytics
        responses = db.query(ClientProfilingResponse).join(QuestionnaireInvite).filter(
            QuestionnaireInvite.status == QuestionnaireInviteStatus.COMPLETED
        )
        if created_by_id:
            responses = responses.filter(QuestionnaireInvite.created_by_id == created_by_id)

        responses_list = responses.all()

        # Calculate averages
        avg_monthly_income = None
        avg_investment_capacity = None
        if responses_list:
            incomes = [r.monthly_income for r in responses_list if r.monthly_income]
            capacities = [r.monthly_investment_capacity for r in responses_list if r.monthly_investment_capacity]

            avg_monthly_income = sum(incomes) / len(incomes) if incomes else None
            avg_investment_capacity = sum(capacities) / len(capacities) if capacities else None

        # Risk category distribution
        risk_dist = {}
        for category in RiskCategory:
            count = len([r for r in responses_list if r.calculated_risk_category == category])
            if count > 0:
                risk_dist[category.value] = count

        # Top goals
        goal_counts = {}
        for response in responses_list:
            if response.financial_goals:
                for goal in response.financial_goals:
                    goal_type = goal.get('goal_type')
                    if goal_type:
                        goal_counts[goal_type] = goal_counts.get(goal_type, 0) + 1

        top_goals = [{"goal_type": k, "count": v} for k, v in sorted(goal_counts.items(), key=lambda x: x[1], reverse=True)[:5]]

        return {
            "total_invites": total_invites,
            "pending": pending,
            "completed": completed,
            "expired": expired,
            "completion_rate": round(completion_rate, 2),
            "avg_monthly_income": round(avg_monthly_income, 2) if avg_monthly_income else None,
            "avg_investment_capacity": round(avg_investment_capacity, 2) if avg_investment_capacity else None,
            "risk_category_distribution": risk_dist,
            "top_goals": top_goals
        }

    @staticmethod
    def check_and_expire_invites(db: Session):
        """
        Check and mark expired invites

        Args:
            db: Database session
        """
        now = datetime.now(timezone.utc)
        expired_invites = db.query(QuestionnaireInvite).filter(
            and_(
                QuestionnaireInvite.expires_at != None,
                QuestionnaireInvite.expires_at < now,
                QuestionnaireInvite.status == QuestionnaireInviteStatus.PENDING
            )
        ).all()

        for invite in expired_invites:
            invite.status = QuestionnaireInviteStatus.EXPIRED

        if expired_invites:
            db.commit()
            logger.info(f"Marked {len(expired_invites)} invites as expired")
