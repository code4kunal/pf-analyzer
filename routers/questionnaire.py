"""
Client Profiling Questionnaire API Endpoints
Handles invite creation, tracking, and public questionnaire submission
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone

from database import get_db
from models import User, QuestionnaireInvite, ClientProfilingResponse, QuestionnaireInviteStatus
from schemas import (
    QuestionnaireInviteCreate, QuestionnaireInviteResponse, QuestionnaireInviteListResponse,
    ClientProfilingSubmission, ClientProfilingResponseDetail, QuestionnaireAnalytics
)
from services.questionnaire_service import QuestionnaireService
from services.enhanced_risk_questionnaire import ENHANCED_QUESTIONNAIRE, RISK_CATEGORIES_DETAILED
import auth

router = APIRouter(prefix="/api/questionnaire", tags=["Client Profiling Questionnaire"])

# ============================================================================
# ADMIN ENDPOINTS (Protected)
# ============================================================================

@router.post("/invites", response_model=QuestionnaireInviteResponse)
async def create_invite(
    invite_data: QuestionnaireInviteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.require_admin)
):
    """
    Create a new questionnaire invite

    - Generates unique secure token
    - Sets expiry date based on expires_in_days
    - Returns complete invite with shareable URL
    """
    try:
        # Create invite
        invite = QuestionnaireService.create_invite(
            db=db,
            invite_data=invite_data,
            created_by_id=current_user.id,
            base_url="https://yourdomain.com"  # TODO: Get from config
        )

        # Build invite URL
        invite_url = f"https://yourdomain.com/questionnaire/{invite.invite_token}"

        # Check if expired
        is_expired = False
        if invite.expires_at and datetime.now(timezone.utc) > invite.expires_at:
            is_expired = True

        # Build response
        response = QuestionnaireInviteResponse(
            id=invite.id,
            invite_token=invite.invite_token,
            recipient_name=invite.recipient_name,
            recipient_email=invite.recipient_email,
            recipient_phone=invite.recipient_phone,
            status=invite.status,
            created_by_id=invite.created_by_id,
            sent_at=invite.sent_at,
            expires_at=invite.expires_at,
            completed_at=invite.completed_at,
            auto_create_prospect=invite.auto_create_prospect,
            created_prospect_id=invite.created_prospect_id,
            notes=invite.notes,
            custom_message=invite.custom_message,
            invite_url=invite_url,
            is_expired=is_expired
        )

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating invite: {str(e)}")


@router.get("/invites", response_model=List[QuestionnaireInviteListResponse])
async def list_invites(
    status: Optional[QuestionnaireInviteStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.require_admin)
):
    """
    List all questionnaire invites with optional filtering

    - Filter by status (PENDING, COMPLETED, EXPIRED)
    - Pagination support
    - Admin only
    """
    try:
        # Check and expire old invites first
        QuestionnaireService.check_and_expire_invites(db)

        # Base query
        query = db.query(QuestionnaireInvite).order_by(QuestionnaireInvite.sent_at.desc())

        # Filter by status
        if status:
            query = query.filter(QuestionnaireInvite.status == status)

        # Pagination
        invites = query.offset(skip).limit(limit).all()

        # Build response
        results = []
        for invite in invites:
            is_expired = False
            if invite.expires_at and datetime.now(timezone.utc) > invite.expires_at and invite.status == QuestionnaireInviteStatus.PENDING:
                is_expired = True

            results.append(QuestionnaireInviteListResponse(
                id=invite.id,
                recipient_name=invite.recipient_name,
                recipient_email=invite.recipient_email,
                status=invite.status,
                sent_at=invite.sent_at,
                expires_at=invite.expires_at,
                completed_at=invite.completed_at,
                created_prospect_id=invite.created_prospect_id,
                is_expired=is_expired
            ))

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing invites: {str(e)}")


@router.get("/invites/{invite_id}", response_model=QuestionnaireInviteResponse)
async def get_invite(
    invite_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.require_admin)
):
    """Get detailed invite information by ID"""
    try:
        invite = db.query(QuestionnaireInvite).filter(QuestionnaireInvite.id == invite_id).first()
        if not invite:
            raise HTTPException(status_code=404, detail="Invite not found")

        # Build invite URL
        invite_url = f"https://yourdomain.com/questionnaire/{invite.invite_token}"

        # Check if expired
        is_expired = False
        if invite.expires_at and datetime.now(timezone.utc) > invite.expires_at:
            is_expired = True

        return QuestionnaireInviteResponse(
            id=invite.id,
            invite_token=invite.invite_token,
            recipient_name=invite.recipient_name,
            recipient_email=invite.recipient_email,
            recipient_phone=invite.recipient_phone,
            status=invite.status,
            created_by_id=invite.created_by_id,
            sent_at=invite.sent_at,
            expires_at=invite.expires_at,
            completed_at=invite.completed_at,
            auto_create_prospect=invite.auto_create_prospect,
            created_prospect_id=invite.created_prospect_id,
            notes=invite.notes,
            custom_message=invite.custom_message,
            invite_url=invite_url,
            is_expired=is_expired
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving invite: {str(e)}")


@router.get("/responses", response_model=List[ClientProfilingResponseDetail])
async def list_responses(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.require_admin)
):
    """
    List all questionnaire responses

    - Shows detailed client profiling data
    - Admin only
    - Sorted by submission date (newest first)
    """
    try:
        responses = db.query(ClientProfilingResponse).order_by(
            ClientProfilingResponse.submitted_at.desc()
        ).offset(skip).limit(limit).all()

        return [ClientProfilingResponseDetail.from_orm(r) for r in responses]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing responses: {str(e)}")


@router.get("/responses/{response_id}", response_model=ClientProfilingResponseDetail)
async def get_response(
    response_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.require_admin)
):
    """Get detailed response by ID"""
    try:
        response = db.query(ClientProfilingResponse).filter(
            ClientProfilingResponse.id == response_id
        ).first()

        if not response:
            raise HTTPException(status_code=404, detail="Response not found")

        return ClientProfilingResponseDetail.from_orm(response)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving response: {str(e)}")


@router.get("/analytics", response_model=QuestionnaireAnalytics)
async def get_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.require_admin)
):
    """
    Get questionnaire analytics

    - Completion rates
    - Average metrics
    - Risk distribution
    - Top goals
    """
    try:
        analytics = QuestionnaireService.get_analytics(db, created_by_id=None)
        return QuestionnaireAnalytics(**analytics)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving analytics: {str(e)}")


@router.delete("/invites/{invite_id}")
async def delete_invite(
    invite_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.require_admin)
):
    """
    Delete an invite

    - Only pending invites can be deleted
    - Completed invites are archived
    """
    try:
        invite = db.query(QuestionnaireInvite).filter(QuestionnaireInvite.id == invite_id).first()
        if not invite:
            raise HTTPException(status_code=404, detail="Invite not found")

        if invite.status == QuestionnaireInviteStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Cannot delete completed invite. Use archive instead.")

        db.delete(invite)
        db.commit()

        return {"success": True, "message": "Invite deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting invite: {str(e)}")


# ============================================================================
# PUBLIC ENDPOINTS (No Authentication Required)
# ============================================================================

@router.get("/public/questionnaire-config")
async def get_questionnaire_config():
    """
    Get questionnaire configuration (public)

    - Returns enhanced questionnaire with all explanations
    - Risk category details
    - No authentication required
    """
    try:
        return {
            "questionnaire": ENHANCED_QUESTIONNAIRE,
            "risk_categories": RISK_CATEGORIES_DETAILED,
            "version": "1.0",
            "total_questions": len(ENHANCED_QUESTIONNAIRE)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading questionnaire: {str(e)}")


@router.get("/public/{token}/validate")
async def validate_invite_token(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Validate invite token (public)

    - Check if token exists and is valid
    - Returns recipient info and validity status
    - No authentication required
    """
    try:
        invite = QuestionnaireService.get_invite_by_token(db, token)

        if not invite:
            raise HTTPException(status_code=404, detail="Invalid invite token")

        # Check validity
        is_valid, error_msg = QuestionnaireService.is_invite_valid(invite)

        return {
            "valid": is_valid,
            "error": error_msg,
            "recipient_name": invite.recipient_name if is_valid else None,
            "recipient_email": invite.recipient_email if is_valid else None,
            "custom_message": invite.custom_message if is_valid else None,
            "expires_at": invite.expires_at.isoformat() if invite.expires_at else None,
            "status": invite.status.value
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validating token: {str(e)}")


@router.post("/public/{token}/submit")
async def submit_questionnaire(
    token: str,
    submission: ClientProfilingSubmission,
    db: Session = Depends(get_db)
):
    """
    Submit completed questionnaire (public)

    - Validates token and responses
    - Calculates risk profile
    - Auto-creates prospect if enabled
    - No authentication required
    """
    try:
        result = QuestionnaireService.submit_questionnaire(
            db=db,
            token=token,
            submission=submission
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error submitting questionnaire: {str(e)}")


@router.get("/public/{token}/status")
async def get_submission_status(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Check if questionnaire has been submitted for this token (public)

    - Returns submission status
    - No authentication required
    """
    try:
        invite = QuestionnaireService.get_invite_by_token(db, token)

        if not invite:
            raise HTTPException(status_code=404, detail="Invalid invite token")

        return {
            "submitted": invite.status == QuestionnaireInviteStatus.COMPLETED,
            "submitted_at": invite.completed_at.isoformat() if invite.completed_at else None,
            "status": invite.status.value
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking status: {str(e)}")
