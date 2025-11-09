"""
Prospects API Router
Admin-only endpoints for prospect management
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime, date
import uuid
import os

from database import get_db
import auth
from models import User, Prospect, ProspectCommunication, ImportBatch, UserRole
from schemas import (
    ProspectCreate, ProspectUpdate, ProspectResponse, ProspectListResponse,
    ProspectDetailResponse, ProspectCommunicationCreate, ProspectCommunicationResponse,
    ProspectConversionRequest, ImportPreviewResponse, ImportConfirmRequest,
    ImportResultResponse, ImportBatchResponse, ProspectFilter, ProspectAnalyticsResponse,
    BulkUpdateRequest, BulkDeleteRequest, BulkAssignRequest
)
from services.prospect_service import ProspectService
from services.prospect_import_service import ProspectImportService
from export_service import excel_export_service

router = APIRouter(prefix="/api/prospects", tags=["prospects"])

# Initialize services
import_service = ProspectImportService()

# ============================================================================
# PROSPECT CRUD ENDPOINTS
# ============================================================================

@router.get("", response_model=dict)
async def list_prospects(
    # Filters
    search: Optional[str] = Query(None),
    status: Optional[List[str]] = Query(None),
    priority: Optional[List[str]] = Query(None),
    source: Optional[List[str]] = Query(None),
    assigned_to_id: Optional[int] = Query(None),
    created_from: Optional[date] = Query(None),
    created_to: Optional[date] = Query(None),
    next_followup_from: Optional[date] = Query(None),
    next_followup_to: Optional[date] = Query(None),
    estimated_value_min: Optional[float] = Query(None),
    estimated_value_max: Optional[float] = Query(None),
    tags: Optional[List[str]] = Query(None),
    is_converted: Optional[bool] = Query(None),
    # Pagination
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    # Dependencies
    current_user: User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """List prospects with filtering and pagination (Admin only)"""

    # Build filters dictionary
    filters = {
        "search": search,
        "status": status,
        "priority": priority,
        "source": source,
        "assigned_to_id": assigned_to_id,
        "created_from": created_from,
        "created_to": created_to,
        "next_followup_from": next_followup_from,
        "next_followup_to": next_followup_to,
        "estimated_value_min": estimated_value_min,
        "estimated_value_max": estimated_value_max,
        "tags": tags,
        "is_converted": is_converted
    }

    # Build query with filters
    query = ProspectService.build_filter_query(db, filters, current_user)

    # Apply sorting
    if hasattr(Prospect, sort_by):
        sort_column = getattr(Prospect, sort_by)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

    # Get total count
    total = query.count()

    # Apply pagination
    prospects = query.options(
        joinedload(Prospect.assigned_to),
        joinedload(Prospect.created_by)
    ).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "items": [ProspectListResponse.from_orm(p) for p in prospects],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

@router.post("", response_model=ProspectResponse, status_code=status.HTTP_201_CREATED)
async def create_prospect(
    prospect_data: ProspectCreate,
    current_user: User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """Create a new prospect (Admin only)"""
    prospect = ProspectService.create_prospect(db, prospect_data, current_user)
    return ProspectResponse.from_orm(prospect)

@router.get("/{prospect_id}", response_model=ProspectDetailResponse)
async def get_prospect(
    prospect_id: int,
    current_user: User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """Get prospect by ID (Admin only)"""
    prospect = db.query(Prospect).options(
        joinedload(Prospect.assigned_to),
        joinedload(Prospect.created_by),
        joinedload(Prospect.converted_by),
        joinedload(Prospect.communications),
        joinedload(Prospect.activities)
    ).filter(Prospect.id == prospect_id).first()

    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")

    return ProspectDetailResponse.from_orm(prospect)

@router.put("/{prospect_id}", response_model=ProspectResponse)
async def update_prospect(
    prospect_id: int,
    prospect_data: ProspectUpdate,
    current_user: User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """Update prospect (Admin only)"""
    try:
        prospect = ProspectService.update_prospect(db, prospect_id, prospect_data, current_user)
        return ProspectResponse.from_orm(prospect)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{prospect_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prospect(
    prospect_id: int,
    current_user: User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """Delete prospect (Admin only)"""
    prospect = db.query(Prospect).filter(Prospect.id == prospect_id).first()
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")

    # Log activity before deleting
    ProspectService.log_activity(
        db, prospect.id, current_user.id,
        "DELETED",
        f"Prospect {prospect.full_name} deleted"
    )

    db.delete(prospect)
    db.commit()

# ============================================================================
# CONVERSION ENDPOINT
# ============================================================================

@router.post("/{prospect_id}/convert", response_model=dict)
async def convert_prospect_to_customer(
    prospect_id: int,
    conversion_data: ProspectConversionRequest,
    current_user: User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """Convert prospect to customer (Admin only)"""
    try:
        customer = ProspectService.convert_to_customer(
            db, prospect_id, current_user,
            conversion_data.relationship_manager_id,
            conversion_data.copy_notes
        )
        return {
            "message": "Prospect converted to customer successfully",
            "customer_id": customer.id,
            "customer_name": customer.full_name
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# COMMUNICATIONS ENDPOINTS
# ============================================================================

@router.post("/{prospect_id}/communications", response_model=ProspectCommunicationResponse)
async def log_communication(
    prospect_id: int,
    communication_data: ProspectCommunicationCreate,
    current_user: User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """Log communication with prospect (Admin only)"""
    prospect = db.query(Prospect).filter(Prospect.id == prospect_id).first()
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")

    communication = ProspectCommunication(
        **communication_data.dict(exclude={"prospect_id"}),
        prospect_id=prospect_id,
        user_id=current_user.id
    )

    db.add(communication)

    # Update prospect contact tracking
    prospect.contact_attempts += 1
    prospect.last_contact_date = datetime.utcnow()
    if not prospect.first_contact_date:
        prospect.first_contact_date = datetime.utcnow()

    # If status is NEW, update to CONTACTED
    if prospect.status.value == "NEW":
        prospect.status = "CONTACTED"

    db.commit()
    db.refresh(communication)

    # Log activity
    ProspectService.log_activity(
        db, prospect.id, current_user.id,
        "COMMUNICATION_LOGGED",
        f"{communication_data.communication_type.value} communication logged"
    )

    return ProspectCommunicationResponse.from_orm(communication)

@router.get("/{prospect_id}/communications", response_model=List[ProspectCommunicationResponse])
async def get_communications(
    prospect_id: int,
    current_user: User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """Get all communications for a prospect (Admin only)"""
    prospect = db.query(Prospect).filter(Prospect.id == prospect_id).first()
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")

    communications = db.query(ProspectCommunication).filter(
        ProspectCommunication.prospect_id == prospect_id
    ).order_by(ProspectCommunication.communication_date.desc()).all()

    return [ProspectCommunicationResponse.from_orm(c) for c in communications]

# ============================================================================
# IMPORT ENDPOINTS
# ============================================================================

@router.post("/import/upload", response_model=ImportPreviewResponse)
async def upload_import_file(
    file: UploadFile = File(...),
    current_user: User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """Upload file for import preview (Admin only)"""

    # Validate file type
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported")

    # Validate file size (max 10MB)
    file_content = await file.read()
    if len(file_content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be less than 10MB")

    # Save temp file
    file_key = import_service.save_temp_file(file_content, file.filename)

    # Read file and suggest mappings
    df = import_service.read_file(file_key)
    suggested_mappings = import_service.suggest_column_mapping(list(df.columns))

    # Get existing emails and phones for duplicate detection
    existing_emails = ProspectService.get_existing_emails(db)
    existing_phones = ProspectService.get_existing_phones(db)

    # Get preview
    preview_data = import_service.preview_import(
        file_key, suggested_mappings, existing_emails, existing_phones
    )

    return ImportPreviewResponse(
        file_key=file_key,
        total_rows=preview_data["total_rows"],
        valid_rows=preview_data["valid_rows"],
        invalid_rows=preview_data["invalid_rows"],
        suggested_mappings=suggested_mappings,
        preview_rows=preview_data["preview_rows"]
    )

@router.post("/import/confirm", response_model=ImportResultResponse)
async def confirm_import(
    import_request: ImportConfirmRequest,
    current_user: User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """Confirm and process import (Admin only)"""

    # Get existing emails and phones
    existing_emails = ProspectService.get_existing_emails(db)
    existing_phones = ProspectService.get_existing_phones(db)

    # Process import
    successful_records, failed_records = import_service.process_import(
        import_request.file_key,
        import_request.column_mappings,
        existing_emails,
        existing_phones,
        import_request.skip_duplicates
    )

    # Create import batch record
    batch_id = str(uuid.uuid4())
    temp_files = [f for f in os.listdir(import_service.temp_dir) if f.startswith(import_request.file_key)]
    file_name = temp_files[0] if temp_files else "unknown"

    import_batch = ImportBatch(
        batch_id=batch_id,
        file_name=file_name,
        file_size=None,
        total_records=len(successful_records) + len(failed_records),
        successful_imports=0,
        failed_imports=len(failed_records),
        errors=[{"row": r["row_number"], "errors": r["errors"]} for r in failed_records],
        imported_by_id=current_user.id,
        mapping_used=import_request.column_mappings
    )

    db.add(import_batch)
    db.flush()

    # Create prospect records
    for record_data in successful_records:
        prospect = Prospect(
            **{k: v for k, v in record_data.items() if k != 'custom_fields'},
            source="IMPORT",
            import_batch_id=batch_id,
            import_file_name=file_name,
            import_date=datetime.utcnow(),
            created_by_id=current_user.id
        )

        # Handle custom fields
        if 'custom_fields' in record_data:
            prospect.custom_fields = record_data['custom_fields']

        db.add(prospect)
        import_batch.successful_imports += 1

    db.commit()

    # Cleanup temp file
    import_service.cleanup_temp_file(import_request.file_key)

    return ImportResultResponse(
        batch_id=batch_id,
        total_records=import_batch.total_records,
        successful_imports=import_batch.successful_imports,
        failed_imports=import_batch.failed_imports,
        errors=import_batch.errors or [],
        message=f"Successfully imported {import_batch.successful_imports} prospects. {import_batch.failed_imports} failed."
    )

@router.get("/import/history", response_model=List[ImportBatchResponse])
async def get_import_history(
    current_user: User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """Get import history (Admin only)"""
    batches = db.query(ImportBatch).options(
        joinedload(ImportBatch.imported_by)
    ).order_by(ImportBatch.created_at.desc()).limit(50).all()

    return [ImportBatchResponse.from_orm(b) for b in batches]

# ============================================================================
# EXPORT ENDPOINT
# ============================================================================

@router.get("/export")
async def export_prospects(
    # Same filters as list endpoint
    search: Optional[str] = Query(None),
    status: Optional[List[str]] = Query(None),
    priority: Optional[List[str]] = Query(None),
    source: Optional[List[str]] = Query(None),
    assigned_to_id: Optional[int] = Query(None),
    created_from: Optional[date] = Query(None),
    created_to: Optional[date] = Query(None),
    current_user: User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """Export prospects to Excel (Admin only)"""

    filters = {
        "search": search,
        "status": status,
        "priority": priority,
        "source": source,
        "assigned_to_id": assigned_to_id,
        "created_from": created_from,
        "created_to": created_to
    }

    # Build query with filters
    query = ProspectService.build_filter_query(db, filters, current_user)
    prospects = query.options(joinedload(Prospect.assigned_to)).all()

    # Generate export file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"prospects_{timestamp}.xlsx"
    output_path = f"./exports/{filename}"

    os.makedirs("./exports", exist_ok=True)

    excel_export_service.export_prospects(prospects, output_path)

    return FileResponse(
        output_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=filename
    )

# ============================================================================
# ANALYTICS ENDPOINT
# ============================================================================

@router.get("/analytics", response_model=ProspectAnalyticsResponse)
async def get_analytics(
    current_user: User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """Get prospect analytics (Admin only)"""
    analytics = ProspectService.get_analytics(db)
    return ProspectAnalyticsResponse(**analytics)

# ============================================================================
# BULK OPERATIONS
# ============================================================================

@router.post("/bulk-update", status_code=status.HTTP_200_OK)
async def bulk_update_prospects(
    bulk_request: BulkUpdateRequest,
    current_user: User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """Bulk update prospects (Admin only)"""
    updated_count = 0

    for prospect_id in bulk_request.prospect_ids:
        try:
            ProspectService.update_prospect(db, prospect_id, bulk_request.updates, current_user)
            updated_count += 1
        except ValueError:
            continue

    return {"message": f"Successfully updated {updated_count} prospects"}

@router.post("/bulk-delete", status_code=status.HTTP_200_OK)
async def bulk_delete_prospects(
    bulk_request: BulkDeleteRequest,
    current_user: User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """Bulk delete prospects (Admin only)"""
    deleted_count = 0

    for prospect_id in bulk_request.prospect_ids:
        prospect = db.query(Prospect).filter(Prospect.id == prospect_id).first()
        if prospect:
            db.delete(prospect)
            deleted_count += 1

    db.commit()

    return {"message": f"Successfully deleted {deleted_count} prospects"}

@router.post("/bulk-assign", status_code=status.HTTP_200_OK)
async def bulk_assign_prospects(
    bulk_request: BulkAssignRequest,
    current_user: User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """Bulk assign prospects to user (Admin only)"""

    # Verify assigned user exists
    assigned_user = db.query(User).filter(User.id == bulk_request.assigned_to_id).first()
    if not assigned_user:
        raise HTTPException(status_code=404, detail="Assigned user not found")

    updated_count = 0

    for prospect_id in bulk_request.prospect_ids:
        prospect = db.query(Prospect).filter(Prospect.id == prospect_id).first()
        if prospect:
            prospect.assigned_to_id = bulk_request.assigned_to_id
            ProspectService.log_activity(
                db, prospect.id, current_user.id,
                "ASSIGNED",
                f"Prospect assigned to {assigned_user.full_name}"
            )
            updated_count += 1

    db.commit()

    return {"message": f"Successfully assigned {updated_count} prospects to {assigned_user.full_name}"}
