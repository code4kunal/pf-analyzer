from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uvicorn
import logging
import os
import shutil
from pathlib import Path

from database import engine, get_db
from models import Base, User, UserRole, Document, DocumentCategory, Commission, Invoice, InvoiceStatus
import schemas
import auth
from config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables (in production, use Alembic migrations)
# Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Customer Management System for Investment Consultancy Firms"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else [settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Create uploads directory if it doesn't exist
os.makedirs(settings.upload_dir, exist_ok=True)

# Import and include routers
from routers import prospects, questionnaire, portfolio
app.include_router(prospects.router)
app.include_router(questionnaire.router)
app.include_router(portfolio.router)

# Validation Error Handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Log and return detailed validation errors"""
    logger.error(f"Validation error on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()}
    )

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for Railway"""
    return {"status": "ok"}

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/api/auth/login", response_model=schemas.LoginResponse, tags=["Authentication"])
async def login(
    login_data: schemas.LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login endpoint - authenticate user and return JWT token
    """
    try:
        # Authenticate user
        user = auth.authenticate_user(db, login_data.email, login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()

        # Create access token
        access_token = auth.create_access_token(
            data={
                "sub": user.email,
                "user_id": user.id,
                "role": user.role.value
            }
        )

        # Log activity
        auth.log_activity(
            db=db,
            entity_type="user",
            entity_id=user.id,
            action="login",
            description=f"{user.full_name} logged in",
            user_id=user.id
        )

        return schemas.LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=user,
            is_temp_password=user.is_temp_password
        )
    except HTTPException:
        # Re-raise HTTP exceptions (like 401 Unauthorized)
        raise
    except Exception as e:
        # Log the actual error for debugging
        import traceback
        print(f"❌ Login error for {login_data.email}: {str(e)}", flush=True)
        print(traceback.format_exc(), flush=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@app.post("/api/auth/change-password", tags=["Authentication"])
async def change_password(
    password_data: schemas.PasswordChangeRequest,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change password - requires old password verification
    """
    # Verify old password
    if not auth.verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )

    # Update password
    current_user.hashed_password = auth.get_password_hash(password_data.new_password)
    current_user.is_temp_password = False
    db.commit()

    # Log activity
    auth.log_activity(
        db=db,
        entity_type="user",
        entity_id=current_user.id,
        action="password_change",
        description=f"{current_user.full_name} changed their password",
        user_id=current_user.id
    )

    return {"message": "Password changed successfully"}

@app.get("/api/auth/me", response_model=schemas.UserResponse, tags=["Authentication"])
async def get_current_user_info(
    current_user: User = Depends(auth.get_current_user)
):
    """
    Get current user information
    """
    return current_user

# ============================================================================
# USER MANAGEMENT ENDPOINTS (Admin Only)
# ============================================================================

@app.post("/api/users/invite", response_model=schemas.UserInviteResponse, tags=["Users"])
async def invite_user(
    user_data: schemas.UserInvite,
    current_user: User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """
    Invite a new user (Admin only)
    - Generates temporary password
    - Sends invitation email
    - Creates user account
    - Returns temporary password for admin to share securely
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )

    # Generate temporary password
    temp_password = auth.generate_temp_password()

    # Create user
    new_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        phone=user_data.phone,
        role=user_data.role,
        hashed_password=auth.get_password_hash(temp_password),
        is_temp_password=True,
        is_active=True,
        created_by_id=current_user.id
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Send invitation email
    try:
        auth.send_invitation_email(new_user, temp_password)
    except Exception as e:
        logger.error(f"Failed to send invitation email: {e}")
        # Don't fail the user creation if email fails

    # Log activity
    auth.log_activity(
        db=db,
        entity_type="user",
        entity_id=new_user.id,
        action="created",
        description=f"{current_user.full_name} invited {new_user.full_name}",
        user_id=current_user.id
    )

    return schemas.UserInviteResponse(
        user=new_user,
        temporary_password=temp_password
    )

@app.get("/api/users", response_model=List[schemas.UserListResponse], tags=["Users"])
async def list_users(
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all users
    - Admins can see all users
    - Employees can see all active users
    """
    query = db.query(User)

    # Employees can only see active users
    if current_user.role == UserRole.EMPLOYEE:
        query = query.filter(User.is_active == True)

    users = query.order_by(User.created_at.desc()).all()
    return users

@app.get("/api/users/{user_id}", response_model=schemas.UserResponse, tags=["Users"])
async def get_user(
    user_id: int,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user details by ID
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user

@app.put("/api/users/{user_id}", response_model=schemas.UserResponse, tags=["Users"])
async def update_user(
    user_id: int,
    user_data: schemas.UserUpdate,
    current_user: User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """
    Update user (Admin only)
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update fields
    if user_data.full_name is not None:
        user.full_name = user_data.full_name
    if user_data.phone is not None:
        user.phone = user_data.phone
    if user_data.is_active is not None:
        user.is_active = user_data.is_active

    db.commit()
    db.refresh(user)

    # Log activity
    auth.log_activity(
        db=db,
        entity_type="user",
        entity_id=user.id,
        action="updated",
        description=f"{current_user.full_name} updated {user.full_name}",
        user_id=current_user.id
    )

    return user

@app.delete("/api/users/{user_id}", tags=["Users"])
async def delete_user(
    user_id: int,
    current_user: User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """
    Delete user (Admin only)
    - Actually just deactivates the user
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Don't allow deleting yourself
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    # Deactivate instead of delete
    user.is_active = False
    db.commit()

    # Log activity
    auth.log_activity(
        db=db,
        entity_type="user",
        entity_id=user.id,
        action="deleted",
        description=f"{current_user.full_name} deactivated {user.full_name}",
        user_id=current_user.id
    )

    return {"message": "User deactivated successfully"}

@app.post("/api/users/{user_id}/reset-password", tags=["Users"])
async def reset_user_password(
    user_id: int,
    current_user: User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """
    Reset user password (Admin only)
    - Generates new temporary password
    - Sends email notification
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Generate new temporary password
    temp_password = auth.generate_temp_password()

    # Update password
    user.hashed_password = auth.get_password_hash(temp_password)
    user.is_temp_password = True
    db.commit()

    # Send email
    try:
        auth.send_password_reset_email(user, temp_password)
    except Exception as e:
        logger.error(f"Failed to send password reset email: {e}")

    # Log activity
    auth.log_activity(
        db=db,
        entity_type="user",
        entity_id=user.id,
        action="password_reset",
        description=f"{current_user.full_name} reset password for {user.full_name}",
        user_id=current_user.id
    )

    return {"message": "Password reset successfully", "temp_password": temp_password}

# ============================================================================
# CUSTOMER MANAGEMENT ENDPOINTS
# ============================================================================

@app.post("/api/customers", response_model=schemas.CustomerResponse, tags=["Customers"])
async def create_customer(
    customer_data: schemas.CustomerCreate,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new customer
    """
    from models import Customer

    # Check if customer with email already exists
    existing = db.query(Customer).filter(Customer.email == customer_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer with this email already exists"
        )

    # Check if PAN already exists (if provided)
    if customer_data.pan_number:
        existing_pan = db.query(Customer).filter(Customer.pan_number == customer_data.pan_number).first()
        if existing_pan:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer with this PAN already exists"
            )

    # Create customer
    customer = Customer(
        **customer_data.dict(),
        created_by_id=current_user.id
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    # Log activity
    auth.log_activity(
        db=db,
        entity_type="customer",
        entity_id=customer.id,
        action="created",
        description=f"{current_user.full_name} created customer {customer.full_name}",
        user_id=current_user.id
    )

    return customer

@app.get("/api/customers", tags=["Customers"])
async def list_customers(
    page: int = 1,
    page_size: int = 20,
    search: str = None,
    status: str = None,
    risk_profile: str = None,
    relationship_manager_id: int = None,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    List customers with pagination and filters
    - Supports search by name, email, phone, PAN
    - Filter by status, risk profile, relationship manager
    """
    from models import Customer, CustomerStatus, RiskProfile
    from sqlalchemy import or_, func
    import math

    query = db.query(Customer)

    # Employees only see customers assigned to them
    if current_user.role == UserRole.EMPLOYEE:
        query = query.filter(Customer.relationship_manager_id == current_user.id)

    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Customer.full_name.ilike(search_term),
                Customer.email.ilike(search_term),
                Customer.phone.ilike(search_term),
                Customer.pan_number.ilike(search_term)
            )
        )

    # Apply status filter
    if status:
        try:
            status_enum = CustomerStatus(status)
            query = query.filter(Customer.status == status_enum)
        except ValueError:
            pass

    # Apply risk profile filter
    if risk_profile:
        try:
            risk_enum = RiskProfile(risk_profile)
            query = query.filter(Customer.risk_profile == risk_enum)
        except ValueError:
            pass

    # Apply relationship manager filter
    if relationship_manager_id:
        query = query.filter(Customer.relationship_manager_id == relationship_manager_id)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    customers = query.order_by(Customer.created_at.desc()).offset(offset).limit(page_size).all()

    # Calculate total pages
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return {
        "items": customers,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }

@app.get("/api/customers/{customer_id}", response_model=schemas.CustomerDetailResponse, tags=["Customers"])
async def get_customer(
    customer_id: int,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get customer details by ID with family members and nominees
    """
    from models import Customer

    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    # Employees can only view their assigned customers
    if current_user.role == UserRole.EMPLOYEE:
        if customer.relationship_manager_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this customer"
            )

    return customer

@app.put("/api/customers/{customer_id}", response_model=schemas.CustomerResponse, tags=["Customers"])
async def update_customer(
    customer_id: int,
    customer_data: schemas.CustomerUpdate,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update customer details
    """
    from models import Customer

    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    # Employees can only update their assigned customers
    if current_user.role == UserRole.EMPLOYEE:
        if customer.relationship_manager_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this customer"
            )

    # Track changes for activity log
    changes = {}

    # Update fields
    update_data = customer_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None and getattr(customer, field) != value:
            changes[field] = {"old": str(getattr(customer, field)), "new": str(value)}
            setattr(customer, field, value)

    db.commit()
    db.refresh(customer)

    # Log activity
    if changes:
        auth.log_activity(
            db=db,
            entity_type="customer",
            entity_id=customer.id,
            action="updated",
            description=f"{current_user.full_name} updated customer {customer.full_name}",
            user_id=current_user.id,
            changes=changes
        )

    return customer

@app.delete("/api/customers/{customer_id}", tags=["Customers"])
async def delete_customer(
    customer_id: int,
    current_user: User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """
    Delete customer (Admin only)
    - Cascading delete removes all related data
    """
    from models import Customer

    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    customer_name = customer.full_name

    # Log activity before deletion
    auth.log_activity(
        db=db,
        entity_type="customer",
        entity_id=customer.id,
        action="deleted",
        description=f"{current_user.full_name} deleted customer {customer_name}",
        user_id=current_user.id
    )

    db.delete(customer)
    db.commit()

    return {"message": "Customer deleted successfully"}

# ============================================================================
# FAMILY MEMBERS & NOMINEES
# ============================================================================

@app.post("/api/customers/{customer_id}/family-members", response_model=schemas.FamilyMemberResponse, tags=["Customers"])
async def add_family_member(
    customer_id: int,
    member_data: schemas.FamilyMemberCreate,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add family member to customer
    """
    from models import Customer, FamilyMember

    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    member = FamilyMember(
        customer_id=customer_id,
        **member_data.dict()
    )

    db.add(member)
    db.commit()
    db.refresh(member)

    return member

@app.delete("/api/customers/{customer_id}/family-members/{member_id}", tags=["Customers"])
async def remove_family_member(
    customer_id: int,
    member_id: int,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove family member
    """
    from models import FamilyMember

    member = db.query(FamilyMember).filter(
        FamilyMember.id == member_id,
        FamilyMember.customer_id == customer_id
    ).first()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Family member not found"
        )

    db.delete(member)
    db.commit()

    return {"message": "Family member removed successfully"}

@app.post("/api/customers/{customer_id}/nominees", response_model=schemas.NomineeResponse, tags=["Customers"])
async def add_nominee(
    customer_id: int,
    nominee_data: schemas.NomineeCreate,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add nominee to customer
    """
    from models import Customer, Nominee

    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    nominee = Nominee(
        customer_id=customer_id,
        **nominee_data.dict()
    )

    db.add(nominee)
    db.commit()
    db.refresh(nominee)

    return nominee

@app.delete("/api/customers/{customer_id}/nominees/{nominee_id}", tags=["Customers"])
async def remove_nominee(
    customer_id: int,
    nominee_id: int,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove nominee
    """
    from models import Nominee

    nominee = db.query(Nominee).filter(
        Nominee.id == nominee_id,
        Nominee.customer_id == customer_id
    ).first()

    if not nominee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nominee not found"
        )

    db.delete(nominee)
    db.commit()

    return {"message": "Nominee removed successfully"}

# ============================================================================
# INVESTMENT TRACKING
# ============================================================================

@app.post("/api/investments", response_model=schemas.InvestmentResponse, tags=["Investments"])
async def create_investment(
    investment_data: schemas.InvestmentCreate,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new investment for a customer
    """
    from models import Investment, Customer

    # Verify customer exists
    customer = db.query(Customer).filter(Customer.id == investment_data.customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    # Calculate returns if current value is provided
    invested_amount = investment_data.invested_amount
    current_value = investment_data.current_value

    returns_absolute = None
    returns_percentage = None

    if current_value:
        returns_absolute = current_value - invested_amount
        returns_percentage = (returns_absolute / invested_amount) * 100 if invested_amount > 0 else 0

    # Create investment
    investment = Investment(
        **investment_data.dict(exclude={'customer_id'}),
        customer_id=investment_data.customer_id,
        returns_absolute=returns_absolute,
        returns_percentage=returns_percentage
    )

    db.add(investment)

    # Update customer's portfolio value
    if current_value:
        customer.current_portfolio_value += current_value
    else:
        customer.current_portfolio_value += invested_amount

    db.commit()
    db.refresh(investment)

    # Log activity
    auth.log_activity(
        db=db,
        entity_type="investment",
        entity_id=investment.id,
        action="created",
        description=f"{current_user.full_name} added investment {investment.investment_name} for {customer.full_name}",
        user_id=current_user.id
    )

    return investment

@app.get("/api/customers/{customer_id}/investments", response_model=List[schemas.InvestmentResponse], tags=["Investments"])
async def get_customer_investments(
    customer_id: int,
    is_active: bool = None,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all investments for a customer
    """
    from models import Investment, Customer

    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    query = db.query(Investment).filter(Investment.customer_id == customer_id)

    if is_active is not None:
        query = query.filter(Investment.is_active == is_active)

    investments = query.order_by(Investment.investment_date.desc()).all()
    return investments

@app.put("/api/investments/{investment_id}", response_model=schemas.InvestmentResponse, tags=["Investments"])
async def update_investment(
    investment_id: int,
    investment_data: schemas.InvestmentUpdate,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update investment details (mainly current value and returns)
    """
    from models import Investment

    investment = db.query(Investment).filter(Investment.id == investment_id).first()
    if not investment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investment not found"
        )

    # Update fields
    update_data = investment_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(investment, field, value)

    # Recalculate returns if current value changed
    if investment_data.current_value is not None:
        investment.returns_absolute = investment.current_value - investment.invested_amount
        investment.returns_percentage = (investment.returns_absolute / investment.invested_amount) * 100 if investment.invested_amount > 0 else 0

    db.commit()
    db.refresh(investment)

    return investment

@app.delete("/api/investments/{investment_id}", tags=["Investments"])
async def delete_investment(
    investment_id: int,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an investment
    """
    from models import Investment

    investment = db.query(Investment).filter(Investment.id == investment_id).first()
    if not investment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investment not found"
        )

    db.delete(investment)
    db.commit()

    return {"message": "Investment deleted successfully"}

# ============================================================================
# COMMUNICATION LOGS
# ============================================================================

@app.post("/api/communications", response_model=schemas.CommunicationResponse, tags=["Communications"])
async def create_communication(
    comm_data: schemas.CommunicationCreate,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Log a communication with a customer
    """
    from models import Communication, Customer

    customer = db.query(Customer).filter(Customer.id == comm_data.customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    communication = Communication(
        **comm_data.dict(),
        user_id=current_user.id
    )

    db.add(communication)
    db.commit()
    db.refresh(communication)

    return communication

@app.get("/api/customers/{customer_id}/communications", response_model=List[schemas.CommunicationResponse], tags=["Communications"])
async def get_customer_communications(
    customer_id: int,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all communications for a customer
    """
    from models import Communication

    communications = db.query(Communication).filter(
        Communication.customer_id == customer_id
    ).order_by(Communication.communication_date.desc()).all()

    return communications

# ============================================================================
# NOTES
# ============================================================================

@app.post("/api/notes", response_model=schemas.NoteResponse, tags=["Notes"])
async def create_note(
    note_data: schemas.NoteCreate,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a note for a customer
    """
    from models import Note, Customer

    customer = db.query(Customer).filter(Customer.id == note_data.customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    note = Note(
        **note_data.dict(),
        created_by_id=current_user.id
    )

    db.add(note)
    db.commit()
    db.refresh(note)

    return note

@app.get("/api/customers/{customer_id}/notes", response_model=List[schemas.NoteResponse], tags=["Notes"])
async def get_customer_notes(
    customer_id: int,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all notes for a customer
    - Private notes only visible to creator
    """
    from models import Note

    query = db.query(Note).filter(Note.customer_id == customer_id)

    # Filter private notes
    if current_user.role != UserRole.ADMIN:
        from sqlalchemy import or_
        query = query.filter(
            or_(
                Note.is_private == False,
                Note.created_by_id == current_user.id
            )
        )

    notes = query.order_by(Note.created_at.desc()).all()
    return notes

@app.put("/api/notes/{note_id}", response_model=schemas.NoteResponse, tags=["Notes"])
async def update_note(
    note_id: int,
    note_data: schemas.NoteUpdate,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a note (only creator can update)
    """
    from models import Note

    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )

    # Only creator can update note
    if note.created_by_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own notes"
        )

    update_data = note_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(note, field, value)

    db.commit()
    db.refresh(note)

    return note

@app.delete("/api/notes/{note_id}", tags=["Notes"])
async def delete_note(
    note_id: int,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a note (only creator can delete)
    """
    from models import Note

    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )

    # Only creator can delete note
    if note.created_by_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own notes"
        )

    db.delete(note)
    db.commit()

    return {"message": "Note deleted successfully"}

# ============================================================================
# ACTIVITY LOGS
# ============================================================================

@app.get("/api/customers/{customer_id}/activities", response_model=List[schemas.ActivityLogResponse], tags=["Activity"])
async def get_customer_activities(
    customer_id: int,
    limit: int = 50,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get activity timeline for a customer
    """
    from models import ActivityLog

    activities = db.query(ActivityLog).filter(
        ActivityLog.entity_type == "customer",
        ActivityLog.entity_id == customer_id
    ).order_by(ActivityLog.created_at.desc()).limit(limit).all()

    return activities

# ============================================================================
# NOTIFICATIONS
# ============================================================================

@app.get("/api/notifications", response_model=List[schemas.NotificationResponse], tags=["Notifications"])
async def get_notifications(
    unread_only: bool = False,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get notifications for current user
    """
    from models import Notification

    query = db.query(Notification).filter(Notification.user_id == current_user.id)

    if unread_only:
        query = query.filter(Notification.is_read == False)

    notifications = query.order_by(Notification.created_at.desc()).limit(50).all()
    return notifications

@app.put("/api/notifications/{notification_id}/read", tags=["Notifications"])
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark notification as read
    """
    from models import Notification

    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )

    notification.is_read = True
    notification.read_at = datetime.utcnow()
    db.commit()

    return {"message": "Notification marked as read"}

# ============================================================================
# CALENDAR & EVENTS
# ============================================================================

@app.post("/api/events", response_model=schemas.EventResponse, tags=["Events"])
async def create_event(
    event_data: schemas.EventCreate,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new event with optional Google Meet link
    """
    from models import Event, Customer, EventParticipant, Notification, NotificationType
    from google_calendar_service import google_calendar_service

    # Create event
    event = Event(
        title=event_data.title,
        event_type=event_data.event_type,
        description=event_data.description,
        start_time=event_data.start_time,
        end_time=event_data.end_time,
        location=event_data.location,
        created_by_id=current_user.id
    )

    # Generate Google Meet link if requested
    if event_data.create_meet_link:
        try:
            meet_link = google_calendar_service.create_meet_link(
                title=event_data.title,
                description=event_data.description or "",
                start_time=event_data.start_time,
                end_time=event_data.end_time,
                attendees=[]  # Will add after getting customer emails
            )
            event.meet_link = meet_link
        except Exception as e:
            logger.error(f"Failed to create Google Meet link: {e}")

    db.add(event)
    db.flush()  # Get event ID before adding participants

    # Add participants
    if event_data.participant_ids:
        for customer_id in event_data.participant_ids:
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
            if customer:
                participant = EventParticipant(
                    event_id=event.id,
                    customer_id=customer_id
                )
                db.add(participant)

                # Create notification for relationship manager
                if customer.relationship_manager_id:
                    notification = Notification(
                        user_id=customer.relationship_manager_id,
                        notification_type=NotificationType.EVENT_REMINDER,
                        title=f"New Event: {event.title}",
                        message=f"Event scheduled with {customer.full_name} on {event.start_time.strftime('%b %d, %Y at %I:%M %p')}",
                        action_url=f"/events/{event.id}",
                        event_id=event.id,
                        customer_id=customer_id
                    )
                    db.add(notification)

    db.commit()
    db.refresh(event)

    # Log activity
    auth.log_activity(
        db=db,
        entity_type="event",
        entity_id=event.id,
        action="created",
        description=f"{current_user.full_name} created event: {event.title}",
        user_id=current_user.id
    )

    return event

@app.get("/api/events", tags=["Events"])
async def list_events(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    event_type: Optional[str] = None,
    is_completed: Optional[bool] = None,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    List events with optional filters
    """
    from models import Event, EventType
    from datetime import datetime

    query = db.query(Event)

    # Employees only see events they created
    if current_user.role == UserRole.EMPLOYEE:
        query = query.filter(Event.created_by_id == current_user.id)

    # Filter by date range
    if start_date:
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        query = query.filter(Event.start_time >= start_dt)

    if end_date:
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        query = query.filter(Event.start_time <= end_dt)

    # Filter by event type
    if event_type:
        try:
            event_type_enum = EventType(event_type)
            query = query.filter(Event.event_type == event_type_enum)
        except ValueError:
            pass

    # Filter by completion status
    if is_completed is not None:
        query = query.filter(Event.is_completed == is_completed)

    events = query.order_by(Event.start_time.desc()).all()
    return events

@app.get("/api/events/upcoming", response_model=List[schemas.EventResponse], tags=["Events"])
async def get_upcoming_events(
    days: int = 7,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get upcoming events for the next N days
    """
    from models import Event
    from datetime import datetime, timedelta

    now = datetime.utcnow()
    end_date = now + timedelta(days=days)

    query = db.query(Event).filter(
        Event.start_time >= now,
        Event.start_time <= end_date,
        Event.is_completed == False
    )

    # Employees only see their events
    if current_user.role == UserRole.EMPLOYEE:
        query = query.filter(Event.created_by_id == current_user.id)

    events = query.order_by(Event.start_time.asc()).all()
    return events

@app.get("/api/events/{event_id}", response_model=schemas.EventResponse, tags=["Events"])
async def get_event(
    event_id: int,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get event details by ID
    """
    from models import Event

    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    # Employees can only view their own events
    if current_user.role == UserRole.EMPLOYEE:
        if event.created_by_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this event"
            )

    return event

@app.put("/api/events/{event_id}", response_model=schemas.EventResponse, tags=["Events"])
async def update_event(
    event_id: int,
    event_data: schemas.EventUpdate,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update event details
    """
    from models import Event, EventParticipant, Customer

    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    # Only creator or admin can update
    if current_user.role == UserRole.EMPLOYEE:
        if event.created_by_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own events"
            )

    # Update basic fields
    update_data = event_data.dict(exclude_unset=True, exclude={'participant_ids'})
    for field, value in update_data.items():
        if value is not None:
            setattr(event, field, value)

    # Update participants if provided
    if event_data.participant_ids is not None:
        # Remove existing participants
        db.query(EventParticipant).filter(EventParticipant.event_id == event_id).delete()

        # Add new participants
        for customer_id in event_data.participant_ids:
            participant = EventParticipant(
                event_id=event_id,
                customer_id=customer_id
            )
            db.add(participant)

    db.commit()
    db.refresh(event)

    # Log activity
    auth.log_activity(
        db=db,
        entity_type="event",
        entity_id=event.id,
        action="updated",
        description=f"{current_user.full_name} updated event: {event.title}",
        user_id=current_user.id
    )

    return event

@app.delete("/api/events/{event_id}", tags=["Events"])
async def delete_event(
    event_id: int,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an event
    """
    from models import Event

    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    # Only creator or admin can delete
    if current_user.role == UserRole.EMPLOYEE:
        if event.created_by_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own events"
            )

    event_title = event.title

    # Log activity before deletion
    auth.log_activity(
        db=db,
        entity_type="event",
        entity_id=event.id,
        action="deleted",
        description=f"{current_user.full_name} deleted event: {event_title}",
        user_id=current_user.id
    )

    db.delete(event)
    db.commit()

    return {"message": "Event deleted successfully"}

@app.post("/api/events/{event_id}/complete", tags=["Events"])
async def mark_event_completed(
    event_id: int,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark an event as completed
    """
    from models import Event

    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    event.is_completed = True
    db.commit()

    # Log activity
    auth.log_activity(
        db=db,
        entity_type="event",
        entity_id=event.id,
        action="completed",
        description=f"{current_user.full_name} marked event as completed: {event.title}",
        user_id=current_user.id
    )

    return {"message": "Event marked as completed"}

@app.get("/api/calendar/month/{year}/{month}", tags=["Calendar"])
async def get_calendar_month(
    year: int,
    month: int,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all events for a specific month (for calendar view)
    """
    from models import Event
    from datetime import datetime
    from calendar import monthrange

    # Get first and last day of month
    first_day = datetime(year, month, 1)
    last_day_num = monthrange(year, month)[1]
    last_day = datetime(year, month, last_day_num, 23, 59, 59)

    query = db.query(Event).filter(
        Event.start_time >= first_day,
        Event.start_time <= last_day
    )

    # Employees only see their events
    if current_user.role == UserRole.EMPLOYEE:
        query = query.filter(Event.created_by_id == current_user.id)

    events = query.order_by(Event.start_time.asc()).all()

    # Group events by day
    events_by_day = {}
    for event in events:
        day = event.start_time.day
        if day not in events_by_day:
            events_by_day[day] = []
        events_by_day[day].append(event)

    return {
        "year": year,
        "month": month,
        "events_by_day": events_by_day,
        "total_events": len(events)
    }

# ============================================================================
# DOCUMENT MANAGEMENT
# ============================================================================

@app.post("/api/documents/upload", response_model=schemas.DocumentResponse, tags=["Documents"])
async def upload_document(
    customer_id: int = Form(...),
    document_name: str = Form(...),
    document_category: DocumentCategory = Form(...),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a document for a customer

    - **customer_id**: ID of the customer
    - **document_name**: Name/title of the document
    - **document_category**: Category (KYC, AGREEMENT, BANK_DETAILS, INVESTMENT_PROOF, OTHER)
    - **description**: Optional description
    - **file**: File to upload
    """
    from models import Customer, ActivityLog

    # Check if customer exists
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # RBAC: Employees can only upload for their customers
    if current_user.role == UserRole.EMPLOYEE and customer.relationship_manager_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to upload documents for this customer")

    # Create uploads directory if it doesn't exist
    upload_dir = Path("uploads") / str(customer_id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_extension = Path(file.filename).suffix
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = upload_dir / safe_filename

    # Save file
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        raise HTTPException(status_code=500, detail="Error saving file")

    # Get file size
    file_size = file_path.stat().st_size

    # Create document record
    document = Document(
        customer_id=customer_id,
        document_name=document_name,
        document_category=document_category,
        description=description,
        file_path=str(file_path),
        file_size=file_size,
        mime_type=file.content_type,
        storage_type="local"
    )

    db.add(document)

    # Log activity
    activity = ActivityLog(
        user_id=current_user.id,
        entity_type="customer",
        entity_id=customer_id,
        action="document_upload",
        description=f"Uploaded document: {document_name} ({document_category.value})"
    )
    db.add(activity)

    db.commit()
    db.refresh(document)

    logger.info(f"Document uploaded: {document.id} for customer {customer_id}")
    return document


@app.get("/api/customers/{customer_id}/documents", response_model=List[schemas.DocumentResponse], tags=["Documents"])
def get_customer_documents(
    customer_id: int,
    document_category: Optional[DocumentCategory] = None,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all documents for a customer

    - **customer_id**: ID of the customer
    - **document_category**: Optional filter by category
    """
    from models import Customer

    # Check if customer exists
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # RBAC: Employees can only view their customers' documents
    if current_user.role == UserRole.EMPLOYEE and customer.relationship_manager_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this customer's documents")

    # Query documents
    query = db.query(Document).filter(Document.customer_id == customer_id)

    if document_category:
        query = query.filter(Document.document_category == document_category)

    documents = query.order_by(Document.uploaded_at.desc()).all()
    return documents


@app.get("/api/documents/{document_id}", response_model=schemas.DocumentResponse, tags=["Documents"])
def get_document_details(
    document_id: int,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Get details of a specific document"""
    from models import Customer

    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # RBAC: Check access
    customer = db.query(Customer).filter(Customer.id == document.customer_id).first()
    if current_user.role == UserRole.EMPLOYEE and customer.relationship_manager_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this document")

    return document


@app.get("/api/documents/{document_id}/download", tags=["Documents"])
def download_document(
    document_id: int,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Download a document file"""
    from models import Customer

    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # RBAC: Check access
    customer = db.query(Customer).filter(Customer.id == document.customer_id).first()
    if current_user.role == UserRole.EMPLOYEE and customer.relationship_manager_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to download this document")

    # Check if file exists
    file_path = Path(document.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on server")

    return FileResponse(
        path=str(file_path),
        filename=document.document_name + Path(document.file_path).suffix,
        media_type=document.mime_type
    )


@app.put("/api/documents/{document_id}", response_model=schemas.DocumentResponse, tags=["Documents"])
def update_document_metadata(
    document_id: int,
    document_name: Optional[str] = None,
    description: Optional[str] = None,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Update document metadata (name and description only)"""
    from models import Customer, ActivityLog

    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # RBAC: Check access
    customer = db.query(Customer).filter(Customer.id == document.customer_id).first()
    if current_user.role == UserRole.EMPLOYEE and customer.relationship_manager_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this document")

    # Update fields
    if document_name:
        document.document_name = document_name
    if description is not None:
        document.description = description

    # Log activity
    activity = ActivityLog(
        user_id=current_user.id,
        entity_type="customer",
        entity_id=document.customer_id,
        action="document_update",
        description=f"Updated document: {document.document_name}"
    )
    db.add(activity)

    db.commit()
    db.refresh(document)

    return document


@app.delete("/api/documents/{document_id}", tags=["Documents"])
def delete_document(
    document_id: int,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a document (Admin only)"""
    from models import Customer, ActivityLog

    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Only admins can delete documents
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can delete documents")

    # Delete file from storage
    try:
        file_path = Path(document.file_path)
        if file_path.exists():
            file_path.unlink()
    except Exception as e:
        logger.warning(f"Could not delete file: {e}")

    # Log activity
    activity = ActivityLog(
        user_id=current_user.id,
        entity_type="customer",
        entity_id=document.customer_id,
        action="document_delete",
        description=f"Deleted document: {document.document_name} ({document.document_category.value})"
    )
    db.add(activity)

    # Delete document record
    db.delete(document)
    db.commit()

    return {"message": "Document deleted successfully"}

# ============================================================================
# COMMISSION MANAGEMENT
# ============================================================================

@app.post("/api/commissions", response_model=schemas.CommissionResponse, tags=["Commissions"])
def create_commission(
    commission: schemas.CommissionCreate,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a commission record

    - **customer_id**: ID of the customer
    - **investment_id**: Optional ID of related investment
    - **commission_type**: Type (Upfront, Trail, Advisory Fee, etc.)
    - **amount**: Commission amount
    - **percentage**: Optional percentage
    - **earned_date**: Date commission was earned
    """
    from models import Customer, ActivityLog

    # Check if customer exists
    customer = db.query(Customer).filter(Customer.id == commission.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # RBAC: Employees can only create for their customers
    if current_user.role == UserRole.EMPLOYEE and customer.relationship_manager_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to create commission for this customer")

    # Create commission
    db_commission = Commission(**commission.dict())
    db.add(db_commission)

    # Log activity
    activity = ActivityLog(
        user_id=current_user.id,
        entity_type="customer",
        entity_id=commission.customer_id,
        action="commission_created",
        description=f"Created commission: {commission.commission_type} - ₹{commission.amount:,.2f}"
    )
    db.add(activity)

    db.commit()
    db.refresh(db_commission)

    logger.info(f"Commission created: {db_commission.id} for customer {commission.customer_id}")
    return db_commission


@app.get("/api/commissions", response_model=List[schemas.CommissionResponse], tags=["Commissions"])
def list_commissions(
    customer_id: Optional[int] = None,
    is_paid: Optional[bool] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all commissions with optional filtering

    - **customer_id**: Filter by customer
    - **is_paid**: Filter by payment status
    - **start_date**: Filter from this date (YYYY-MM-DD)
    - **end_date**: Filter to this date (YYYY-MM-DD)
    """
    from models import Customer
    from datetime import datetime

    query = db.query(Commission)

    # RBAC: Employees see only their customers' commissions
    if current_user.role == UserRole.EMPLOYEE:
        customer_ids = db.query(Customer.id).filter(
            Customer.relationship_manager_id == current_user.id
        ).all()
        customer_ids = [cid[0] for cid in customer_ids]
        query = query.filter(Commission.customer_id.in_(customer_ids))

    # Apply filters
    if customer_id:
        query = query.filter(Commission.customer_id == customer_id)

    if is_paid is not None:
        query = query.filter(Commission.is_paid == is_paid)

    if start_date:
        query = query.filter(Commission.earned_date >= datetime.strptime(start_date, "%Y-%m-%d").date())

    if end_date:
        query = query.filter(Commission.earned_date <= datetime.strptime(end_date, "%Y-%m-%d").date())

    commissions = query.order_by(Commission.earned_date.desc()).offset(skip).limit(limit).all()
    return commissions


@app.get("/api/commissions/{commission_id}", response_model=schemas.CommissionResponse, tags=["Commissions"])
def get_commission(
    commission_id: int,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Get commission details"""
    from models import Customer

    commission = db.query(Commission).filter(Commission.id == commission_id).first()
    if not commission:
        raise HTTPException(status_code=404, detail="Commission not found")

    # RBAC: Check access
    customer = db.query(Customer).filter(Customer.id == commission.customer_id).first()
    if current_user.role == UserRole.EMPLOYEE and customer.relationship_manager_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this commission")

    return commission


@app.put("/api/commissions/{commission_id}", response_model=schemas.CommissionResponse, tags=["Commissions"])
def update_commission(
    commission_id: int,
    commission_update: schemas.CommissionUpdate,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Update commission (mark as paid, add payment date, notes)"""
    from models import Customer, ActivityLog

    commission = db.query(Commission).filter(Commission.id == commission_id).first()
    if not commission:
        raise HTTPException(status_code=404, detail="Commission not found")

    # RBAC: Check access
    customer = db.query(Customer).filter(Customer.id == commission.customer_id).first()
    if current_user.role == UserRole.EMPLOYEE and customer.relationship_manager_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this commission")

    # Update fields
    update_data = commission_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(commission, field, value)

    # Log activity if marked as paid
    if commission_update.is_paid and not commission.is_paid:
        activity = ActivityLog(
            user_id=current_user.id,
            entity_type="customer",
            entity_id=commission.customer_id,
            action="commission_paid",
            description=f"Marked commission as paid: {commission.commission_type} - ₹{commission.amount:,.2f}"
        )
        db.add(activity)

    db.commit()
    db.refresh(commission)

    return commission


@app.delete("/api/commissions/{commission_id}", tags=["Commissions"])
def delete_commission(
    commission_id: int,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Delete commission (Admin only)"""
    from models import ActivityLog

    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can delete commissions")

    commission = db.query(Commission).filter(Commission.id == commission_id).first()
    if not commission:
        raise HTTPException(status_code=404, detail="Commission not found")

    # Log activity
    activity = ActivityLog(
        user_id=current_user.id,
        entity_type="customer",
        entity_id=commission.customer_id,
        action="commission_deleted",
        description=f"Deleted commission: {commission.commission_type} - ₹{commission.amount:,.2f}"
    )
    db.add(activity)

    db.delete(commission)
    db.commit()

    return {"message": "Commission deleted successfully"}

# ============================================================================
# INVOICE MANAGEMENT
# ============================================================================

def generate_invoice_number(db: Session) -> str:
    """Generate unique invoice number in format INV-YYYYMM-XXXX"""
    from datetime import datetime

    now = datetime.now()
    prefix = f"INV-{now.strftime('%Y%m')}"

    # Get count of invoices this month
    latest = db.query(Invoice).filter(
        Invoice.invoice_number.like(f"{prefix}%")
    ).order_by(Invoice.invoice_number.desc()).first()

    if latest:
        # Extract number and increment
        last_num = int(latest.invoice_number.split('-')[-1])
        new_num = last_num + 1
    else:
        new_num = 1

    return f"{prefix}-{new_num:04d}"


@app.post("/api/invoices", response_model=schemas.InvoiceResponse, tags=["Invoices"])
def create_invoice(
    invoice: schemas.InvoiceCreate,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create an invoice with auto-generated invoice number

    - **customer_id**: ID of the customer
    - **invoice_date**: Date of invoice
    - **due_date**: Payment due date
    - **line_items**: List of invoice line items
    - **subtotal**: Subtotal amount
    - **tax_amount**: Tax amount
    - **total_amount**: Total amount
    """
    from models import Customer, ActivityLog

    # Check if customer exists
    customer = db.query(Customer).filter(Customer.id == invoice.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # RBAC: Employees can only create for their customers
    if current_user.role == UserRole.EMPLOYEE and customer.relationship_manager_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to create invoice for this customer")

    # Generate invoice number
    invoice_number = generate_invoice_number(db)

    # Create invoice
    invoice_data = invoice.dict()
    invoice_data['invoice_number'] = invoice_number
    invoice_data['status'] = InvoiceStatus.DRAFT

    db_invoice = Invoice(**invoice_data)
    db.add(db_invoice)

    # Log activity
    activity = ActivityLog(
        user_id=current_user.id,
        entity_type="customer",
        entity_id=invoice.customer_id,
        action="invoice_created",
        description=f"Created invoice {invoice_number} for ₹{invoice.total_amount:,.2f}"
    )
    db.add(activity)

    db.commit()
    db.refresh(db_invoice)

    logger.info(f"Invoice created: {invoice_number} for customer {invoice.customer_id}")
    return db_invoice


@app.get("/api/invoices", response_model=List[schemas.InvoiceResponse], tags=["Invoices"])
def list_invoices(
    customer_id: Optional[int] = None,
    status: Optional[InvoiceStatus] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all invoices with optional filtering

    - **customer_id**: Filter by customer
    - **status**: Filter by invoice status
    - **start_date**: Filter from this date (YYYY-MM-DD)
    - **end_date**: Filter to this date (YYYY-MM-DD)
    """
    from models import Customer
    from datetime import datetime

    query = db.query(Invoice)

    # RBAC: Employees see only their customers' invoices
    if current_user.role == UserRole.EMPLOYEE:
        customer_ids = db.query(Customer.id).filter(
            Customer.relationship_manager_id == current_user.id
        ).all()
        customer_ids = [cid[0] for cid in customer_ids]
        query = query.filter(Invoice.customer_id.in_(customer_ids))

    # Apply filters
    if customer_id:
        query = query.filter(Invoice.customer_id == customer_id)

    if status:
        query = query.filter(Invoice.status == status)

    if start_date:
        query = query.filter(Invoice.invoice_date >= datetime.strptime(start_date, "%Y-%m-%d").date())

    if end_date:
        query = query.filter(Invoice.invoice_date <= datetime.strptime(end_date, "%Y-%m-%d").date())

    invoices = query.order_by(Invoice.invoice_date.desc()).offset(skip).limit(limit).all()
    return invoices


@app.get("/api/invoices/{invoice_id}", response_model=schemas.InvoiceResponse, tags=["Invoices"])
def get_invoice(
    invoice_id: int,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Get invoice details"""
    from models import Customer

    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # RBAC: Check access
    customer = db.query(Customer).filter(Customer.id == invoice.customer_id).first()
    if current_user.role == UserRole.EMPLOYEE and customer.relationship_manager_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this invoice")

    return invoice


@app.put("/api/invoices/{invoice_id}", response_model=schemas.InvoiceResponse, tags=["Invoices"])
def update_invoice(
    invoice_id: int,
    invoice_update: schemas.InvoiceUpdate,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Update invoice (status, payment info)"""
    from models import Customer, ActivityLog

    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # RBAC: Check access
    customer = db.query(Customer).filter(Customer.id == invoice.customer_id).first()
    if current_user.role == UserRole.EMPLOYEE and customer.relationship_manager_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this invoice")

    # Update fields
    update_data = invoice_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(invoice, field, value)

    # Log activity if status changed
    if invoice_update.status:
        activity = ActivityLog(
            user_id=current_user.id,
            entity_type="customer",
            entity_id=invoice.customer_id,
            action="invoice_updated",
            description=f"Updated invoice {invoice.invoice_number} status to {invoice_update.status.value}"
        )
        db.add(activity)

    db.commit()
    db.refresh(invoice)

    return invoice


@app.post("/api/invoices/{invoice_id}/mark-paid", response_model=schemas.InvoiceResponse, tags=["Invoices"])
def mark_invoice_paid(
    invoice_id: int,
    payment_date: Optional[str] = None,
    payment_method: Optional[str] = None,
    payment_reference: Optional[str] = None,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Mark invoice as paid"""
    from models import Customer, ActivityLog
    from datetime import datetime

    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # RBAC: Check access
    customer = db.query(Customer).filter(Customer.id == invoice.customer_id).first()
    if current_user.role == UserRole.EMPLOYEE and customer.relationship_manager_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this invoice")

    # Update invoice
    invoice.status = InvoiceStatus.PAID
    invoice.paid_amount = invoice.total_amount
    invoice.payment_date = datetime.strptime(payment_date, "%Y-%m-%d").date() if payment_date else datetime.now().date()

    if payment_method:
        invoice.payment_method = payment_method
    if payment_reference:
        invoice.payment_reference = payment_reference

    # Log activity
    activity = ActivityLog(
        user_id=current_user.id,
        entity_type="customer",
        entity_id=invoice.customer_id,
        action="invoice_paid",
        description=f"Marked invoice {invoice.invoice_number} as paid - ₹{invoice.total_amount:,.2f}"
    )
    db.add(activity)

    db.commit()
    db.refresh(invoice)

    return invoice


@app.post("/api/invoices/{invoice_id}/send", response_model=schemas.InvoiceResponse, tags=["Invoices"])
def send_invoice(
    invoice_id: int,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Mark invoice as sent"""
    from models import Customer, ActivityLog

    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # RBAC: Check access
    customer = db.query(Customer).filter(Customer.id == invoice.customer_id).first()
    if current_user.role == UserRole.EMPLOYEE and customer.relationship_manager_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to send this invoice")

    # Update status
    invoice.status = InvoiceStatus.SENT

    # Log activity
    activity = ActivityLog(
        user_id=current_user.id,
        entity_type="customer",
        entity_id=invoice.customer_id,
        action="invoice_sent",
        description=f"Sent invoice {invoice.invoice_number} to customer"
    )
    db.add(activity)

    db.commit()
    db.refresh(invoice)

    return invoice


@app.delete("/api/invoices/{invoice_id}", tags=["Invoices"])
def delete_invoice(
    invoice_id: int,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Delete invoice (Admin only)"""
    from models import ActivityLog

    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can delete invoices")

    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Log activity
    activity = ActivityLog(
        user_id=current_user.id,
        entity_type="customer",
        entity_id=invoice.customer_id,
        action="invoice_deleted",
        description=f"Deleted invoice {invoice.invoice_number}"
    )
    db.add(activity)

    db.delete(invoice)
    db.commit()

    return {"message": "Invoice deleted successfully"}


@app.get("/api/invoices/{invoice_id}/pdf", tags=["Invoices"])
def download_invoice_pdf(
    invoice_id: int,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Generate and download invoice PDF"""
    from models import Customer
    from invoice_pdf_service import pdf_generator

    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # RBAC: Check access
    customer = db.query(Customer).filter(Customer.id == invoice.customer_id).first()
    if current_user.role == UserRole.EMPLOYEE and customer.relationship_manager_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to download this invoice")

    # Create invoices directory if it doesn't exist
    pdf_dir = Path("invoices")
    pdf_dir.mkdir(exist_ok=True)

    # Generate PDF
    pdf_filename = f"{invoice.invoice_number}.pdf"
    pdf_path = pdf_dir / pdf_filename

    try:
        pdf_generator.generate_invoice_pdf(invoice, customer, str(pdf_path))

        return FileResponse(
            path=str(pdf_path),
            filename=pdf_filename,
            media_type='application/pdf'
        )
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        raise HTTPException(status_code=500, detail="Error generating invoice PDF")

# ============================================================================
# REPORTS & ANALYTICS
# ============================================================================

@app.get("/api/reports/commission-summary", tags=["Reports"])
def get_commission_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    customer_id: Optional[int] = None,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get commission summary report

    - **start_date**: Filter from this date (YYYY-MM-DD)
    - **end_date**: Filter to this date (YYYY-MM-DD)
    - **customer_id**: Filter by customer
    """
    from models import Customer
    from datetime import datetime
    from sqlalchemy import func

    query = db.query(Commission)

    # RBAC: Employees see only their customers' commissions
    if current_user.role == UserRole.EMPLOYEE:
        customer_ids = db.query(Customer.id).filter(
            Customer.relationship_manager_id == current_user.id
        ).all()
        customer_ids = [cid[0] for cid in customer_ids]
        query = query.filter(Commission.customer_id.in_(customer_ids))

    # Apply filters
    if customer_id:
        query = query.filter(Commission.customer_id == customer_id)

    if start_date:
        query = query.filter(Commission.earned_date >= datetime.strptime(start_date, "%Y-%m-%d").date())

    if end_date:
        query = query.filter(Commission.earned_date <= datetime.strptime(end_date, "%Y-%m-%d").date())

    # Get all commissions
    commissions = query.all()

    # Calculate summary
    total_commissions = len(commissions)
    total_amount = sum(c.amount for c in commissions)
    paid_amount = sum(c.amount for c in commissions if c.is_paid)
    pending_amount = total_amount - paid_amount
    paid_count = len([c for c in commissions if c.is_paid])
    pending_count = total_commissions - paid_count

    # Group by commission type
    by_type = {}
    for commission in commissions:
        comm_type = commission.commission_type
        if comm_type not in by_type:
            by_type[comm_type] = {
                "count": 0,
                "total_amount": 0,
                "paid_amount": 0
            }
        by_type[comm_type]["count"] += 1
        by_type[comm_type]["total_amount"] += commission.amount
        if commission.is_paid:
            by_type[comm_type]["paid_amount"] += commission.amount

    return {
        "summary": {
            "total_commissions": total_commissions,
            "total_amount": round(total_amount, 2),
            "paid_amount": round(paid_amount, 2),
            "pending_amount": round(pending_amount, 2),
            "paid_count": paid_count,
            "pending_count": pending_count
        },
        "by_type": by_type,
        "filters": {
            "start_date": start_date,
            "end_date": end_date,
            "customer_id": customer_id
        }
    }


@app.get("/api/dashboard/stats", tags=["Dashboard"])
def get_dashboard_stats(
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive dashboard statistics

    Returns:
    - Customer metrics (total, active, prospective)
    - Investment metrics (total value, count)
    - Commission metrics (total, paid, pending)
    - Invoice metrics (total revenue, outstanding)
    - Recent activities
    - Upcoming events
    """
    from models import Customer, Investment, Event, ActivityLog, Notification
    from datetime import datetime, timedelta
    from sqlalchemy import func

    # RBAC: Get customer scope
    if current_user.role == UserRole.EMPLOYEE:
        customer_filter = Customer.relationship_manager_id == current_user.id
    else:
        customer_filter = True  # Admin sees all

    # Customer Metrics
    total_customers = db.query(func.count(Customer.id)).filter(customer_filter).scalar()
    active_customers = db.query(func.count(Customer.id)).filter(
        customer_filter, Customer.status == "ACTIVE"
    ).scalar()
    prospective_customers = db.query(func.count(Customer.id)).filter(
        customer_filter, Customer.status == "PROSPECTIVE"
    ).scalar()

    # Investment Metrics
    if current_user.role == UserRole.EMPLOYEE:
        customer_ids = db.query(Customer.id).filter(customer_filter).all()
        customer_ids = [cid[0] for cid in customer_ids]
        investment_filter = Investment.customer_id.in_(customer_ids)
    else:
        investment_filter = True

    total_investments = db.query(func.count(Investment.id)).filter(investment_filter).scalar()
    total_invested = db.query(func.sum(Investment.invested_amount)).filter(investment_filter).scalar() or 0
    total_current_value = db.query(func.sum(Investment.current_value)).filter(investment_filter).scalar() or 0

    # Commission Metrics
    commission_query = db.query(Commission)
    if current_user.role == UserRole.EMPLOYEE:
        commission_query = commission_query.filter(Commission.customer_id.in_(customer_ids))

    total_commissions = db.query(func.sum(Commission.amount)).filter(
        commission_query.whereclause if commission_query.whereclause is not None else True
    ).scalar() or 0
    paid_commissions = db.query(func.sum(Commission.amount)).filter(
        commission_query.whereclause if commission_query.whereclause is not None else True,
        Commission.is_paid == True
    ).scalar() or 0
    pending_commissions = total_commissions - paid_commissions

    # Invoice Metrics
    invoice_query = db.query(Invoice)
    if current_user.role == UserRole.EMPLOYEE:
        invoice_query = invoice_query.filter(Invoice.customer_id.in_(customer_ids))

    total_invoices = db.query(func.count(Invoice.id)).filter(
        invoice_query.whereclause if invoice_query.whereclause is not None else True
    ).scalar()
    total_revenue = db.query(func.sum(Invoice.total_amount)).filter(
        invoice_query.whereclause if invoice_query.whereclause is not None else True
    ).scalar() or 0
    paid_revenue = db.query(func.sum(Invoice.paid_amount)).filter(
        invoice_query.whereclause if invoice_query.whereclause is not None else True
    ).scalar() or 0
    outstanding_revenue = total_revenue - paid_revenue

    # Recent Activities (last 10)
    activity_query = db.query(ActivityLog)
    if current_user.role == UserRole.EMPLOYEE:
        activity_query = activity_query.filter(
            ActivityLog.user_id == current_user.id
        )
    recent_activities = activity_query.order_by(ActivityLog.created_at.desc()).limit(10).all()

    # Upcoming Events (next 7 days)
    event_query = db.query(Event).filter(
        Event.start_time >= datetime.now(),
        Event.start_time <= datetime.now() + timedelta(days=7)
    )
    if current_user.role == UserRole.EMPLOYEE:
        event_query = event_query.filter(Event.created_by == current_user.id)
    upcoming_events = event_query.order_by(Event.start_time).limit(5).all()

    # Unread Notifications
    unread_notifications = db.query(func.count(Notification.id)).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).scalar()

    return {
        "customers": {
            "total": total_customers,
            "active": active_customers,
            "prospective": prospective_customers,
            "inactive": total_customers - active_customers - prospective_customers
        },
        "investments": {
            "total_count": total_investments,
            "total_invested": round(total_invested, 2),
            "total_current_value": round(total_current_value, 2),
            "total_returns": round(total_current_value - total_invested, 2),
            "return_percentage": round(((total_current_value - total_invested) / total_invested * 100) if total_invested > 0 else 0, 2)
        },
        "commissions": {
            "total": round(total_commissions, 2),
            "paid": round(paid_commissions, 2),
            "pending": round(pending_commissions, 2)
        },
        "invoices": {
            "total_count": total_invoices,
            "total_revenue": round(total_revenue, 2),
            "paid_revenue": round(paid_revenue, 2),
            "outstanding_revenue": round(outstanding_revenue, 2)
        },
        "recent_activities": [
            {
                "id": activity.id,
                "action": activity.action,
                "description": activity.description,
                "created_at": activity.created_at.isoformat()
            }
            for activity in recent_activities
        ],
        "upcoming_events": [
            {
                "id": event.id,
                "title": event.title,
                "start_time": event.start_time.isoformat(),
                "event_type": event.event_type
            }
            for event in upcoming_events
        ],
        "notifications": {
            "unread_count": unread_notifications
        }
    }


@app.get("/api/reports/revenue", tags=["Reports"])
def get_revenue_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get revenue report from invoices

    - **start_date**: Filter from this date (YYYY-MM-DD)
    - **end_date**: Filter to this date (YYYY-MM-DD)
    """
    from models import Customer
    from datetime import datetime

    query = db.query(Invoice)

    # RBAC: Employees see only their customers' invoices
    if current_user.role == UserRole.EMPLOYEE:
        customer_ids = db.query(Customer.id).filter(
            Customer.relationship_manager_id == current_user.id
        ).all()
        customer_ids = [cid[0] for cid in customer_ids]
        query = query.filter(Invoice.customer_id.in_(customer_ids))

    # Apply filters
    if start_date:
        query = query.filter(Invoice.invoice_date >= datetime.strptime(start_date, "%Y-%m-%d").date())

    if end_date:
        query = query.filter(Invoice.invoice_date <= datetime.strptime(end_date, "%Y-%m-%d").date())

    # Get all invoices
    invoices = query.all()

    # Calculate summary
    total_invoices = len(invoices)
    total_revenue = sum(i.total_amount for i in invoices)
    paid_revenue = sum(i.paid_amount for i in invoices)
    outstanding_revenue = total_revenue - paid_revenue

    # Group by status
    by_status = {}
    for invoice in invoices:
        status = invoice.status.value
        if status not in by_status:
            by_status[status] = {
                "count": 0,
                "total_amount": 0
            }
        by_status[status]["count"] += 1
        by_status[status]["total_amount"] += invoice.total_amount

    # Calculate tax collected
    total_tax = sum(i.tax_amount for i in invoices)

    return {
        "summary": {
            "total_invoices": total_invoices,
            "total_revenue": round(total_revenue, 2),
            "paid_revenue": round(paid_revenue, 2),
            "outstanding_revenue": round(outstanding_revenue, 2),
            "total_tax_collected": round(total_tax, 2)
        },
        "by_status": by_status,
        "filters": {
            "start_date": start_date,
            "end_date": end_date
        }
    }


@app.get("/api/reports/customer-acquisition", tags=["Reports"])
def get_customer_acquisition_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Customer acquisition report

    - **start_date**: Filter from this date (YYYY-MM-DD)
    - **end_date**: Filter to this date (YYYY-MM-DD)
    """
    from models import Customer
    from datetime import datetime
    from collections import defaultdict

    query = db.query(Customer)

    # RBAC: Employees see only their customers
    if current_user.role == UserRole.EMPLOYEE:
        query = query.filter(Customer.relationship_manager_id == current_user.id)

    # Apply filters
    if start_date:
        query = query.filter(Customer.created_at >= datetime.strptime(start_date, "%Y-%m-%d"))
    if end_date:
        query = query.filter(Customer.created_at <= datetime.strptime(end_date, "%Y-%m-%d"))

    customers = query.all()

    # Group by month
    by_month = defaultdict(int)
    by_status = defaultdict(int)
    by_risk_profile = defaultdict(int)

    for customer in customers:
        month_key = customer.created_at.strftime("%Y-%m")
        by_month[month_key] += 1
        by_status[customer.status.value] += 1
        if customer.risk_profile:
            by_risk_profile[customer.risk_profile.value] += 1

    return {
        "summary": {
            "total_customers": len(customers),
            "by_month": dict(by_month),
            "by_status": dict(by_status),
            "by_risk_profile": dict(by_risk_profile)
        },
        "filters": {
            "start_date": start_date,
            "end_date": end_date
        }
    }


@app.get("/api/reports/customer-portfolio", tags=["Reports"])
def get_customer_portfolio_report(
    limit: int = 10,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Customer portfolio analysis - Top customers by portfolio value
    """
    from models import Customer, Investment
    from sqlalchemy import func

    query = db.query(
        Customer.id,
        Customer.full_name,
        Customer.email,
        func.sum(Investment.current_value).label('total_value'),
        func.count(Investment.id).label('investment_count')
    ).join(Investment, Customer.id == Investment.customer_id)

    # RBAC: Employees see only their customers
    if current_user.role == UserRole.EMPLOYEE:
        query = query.filter(Customer.relationship_manager_id == current_user.id)

    top_customers = query.group_by(
        Customer.id, Customer.full_name, Customer.email
    ).order_by(func.sum(Investment.current_value).desc()).limit(limit).all()

    # Calculate average portfolio size
    all_portfolios = db.query(func.sum(Investment.current_value)).join(
        Customer, Customer.id == Investment.customer_id
    )
    if current_user.role == UserRole.EMPLOYEE:
        all_portfolios = all_portfolios.filter(Customer.relationship_manager_id == current_user.id)

    total_value = all_portfolios.scalar() or 0
    customer_count = db.query(func.count(func.distinct(Investment.customer_id))).filter(
        Investment.customer_id.in_(
            db.query(Customer.id).filter(
                Customer.relationship_manager_id == current_user.id if current_user.role == UserRole.EMPLOYEE else True
            )
        )
    ).scalar() or 1

    return {
        "top_customers": [
            {
                "customer_id": c.id,
                "name": c.full_name,
                "email": c.email,
                "total_portfolio_value": round(c.total_value or 0, 2),
                "investment_count": c.investment_count
            }
            for c in top_customers
        ],
        "summary": {
            "average_portfolio_size": round(total_value / customer_count, 2),
            "total_portfolio_value": round(total_value, 2),
            "customers_with_investments": customer_count
        }
    }


@app.get("/api/reports/investment-performance", tags=["Reports"])
def get_investment_performance_report(
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Investment performance analysis"""
    from models import Customer, Investment
    from sqlalchemy import func

    query = db.query(Investment).join(Customer, Customer.id == Investment.customer_id)

    # RBAC: Employees see only their customers' investments
    if current_user.role == UserRole.EMPLOYEE:
        query = query.filter(Customer.relationship_manager_id == current_user.id)

    investments = query.all()

    # Calculate metrics
    total_invested = sum(i.invested_amount for i in investments)
    total_current = sum(i.current_value or i.invested_amount for i in investments)
    total_returns = total_current - total_invested

    # Group by category
    by_category = {}
    for inv in investments:
        cat = inv.investment_type.value
        if cat not in by_category:
            by_category[cat] = {
                "count": 0,
                "invested": 0,
                "current_value": 0,
                "returns": 0
            }
        by_category[cat]["count"] += 1
        by_category[cat]["invested"] += inv.invested_amount
        by_category[cat]["current_value"] += inv.current_value or inv.invested_amount
        by_category[cat]["returns"] += (inv.current_value or inv.invested_amount) - inv.invested_amount

    # Calculate returns percentage for each category
    for cat in by_category:
        invested = by_category[cat]["invested"]
        if invested > 0:
            by_category[cat]["return_percentage"] = round(
                (by_category[cat]["returns"] / invested * 100), 2
            )
        else:
            by_category[cat]["return_percentage"] = 0

    # Find best and worst performing
    sorted_investments = sorted(
        investments,
        key=lambda x: ((x.current_value or x.invested_amount) - x.invested_amount) / x.invested_amount if x.invested_amount > 0 else 0,
        reverse=True
    )

    best_performing = sorted_investments[:5] if len(sorted_investments) >= 5 else sorted_investments
    worst_performing = sorted_investments[-5:] if len(sorted_investments) >= 5 else []

    return {
        "summary": {
            "total_investments": len(investments),
            "total_invested": round(total_invested, 2),
            "total_current_value": round(total_current, 2),
            "total_returns": round(total_returns, 2),
            "overall_return_percentage": round((total_returns / total_invested * 100) if total_invested > 0 else 0, 2)
        },
        "by_category": by_category,
        "best_performing": [
            {
                "investment_name": inv.investment_name,
                "category": inv.investment_type.value,
                "invested": inv.invested_amount,
                "current_value": inv.current_value or inv.invested_amount,
                "returns": (inv.current_value or inv.invested_amount) - inv.invested_amount,
                "return_percentage": round(
                    ((inv.current_value or inv.invested_amount) - inv.invested_amount) / inv.invested_amount * 100,
                    2
                ) if inv.invested_amount > 0 else 0
            }
            for inv in best_performing
        ],
        "worst_performing": [
            {
                "investment_name": inv.investment_name,
                "category": inv.investment_type.value,
                "invested": inv.invested_amount,
                "current_value": inv.current_value or inv.invested_amount,
                "returns": (inv.current_value or inv.invested_amount) - inv.invested_amount,
                "return_percentage": round(
                    ((inv.current_value or inv.invested_amount) - inv.invested_amount) / inv.invested_amount * 100,
                    2
                ) if inv.invested_amount > 0 else 0
            }
            for inv in worst_performing
        ]
    }


@app.get("/api/reports/activity-summary", tags=["Reports"])
def get_activity_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Activity log summary and analytics"""
    from models import ActivityLog
    from datetime import datetime
    from collections import defaultdict

    query = db.query(ActivityLog)

    # RBAC: Employees see only their activities
    if current_user.role == UserRole.EMPLOYEE:
        query = query.filter(ActivityLog.user_id == current_user.id)

    # Apply filters
    if start_date:
        query = query.filter(ActivityLog.created_at >= datetime.strptime(start_date, "%Y-%m-%d"))
    if end_date:
        query = query.filter(ActivityLog.created_at <= datetime.strptime(end_date, "%Y-%m-%d"))

    activities = query.all()

    # Group by action
    by_action = defaultdict(int)
    by_entity_type = defaultdict(int)
    by_date = defaultdict(int)

    for activity in activities:
        by_action[activity.action] += 1
        by_entity_type[activity.entity_type] += 1
        date_key = activity.created_at.strftime("%Y-%m-%d")
        by_date[date_key] += 1

    return {
        "summary": {
            "total_activities": len(activities),
            "by_action": dict(by_action),
            "by_entity_type": dict(by_entity_type),
            "by_date": dict(sorted(by_date.items()))
        },
        "filters": {
            "start_date": start_date,
            "end_date": end_date
        }
    }

# ============================================================================
# EXCEL EXPORTS
# ============================================================================

@app.get("/api/exports/customers", tags=["Exports"])
def export_customers_to_excel(
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Export customers to Excel file"""
    from models import Customer
    from export_service import excel_export_service

    query = db.query(Customer)

    # RBAC: Employees see only their customers
    if current_user.role == UserRole.EMPLOYEE:
        query = query.filter(Customer.relationship_manager_id == current_user.id)

    customers = query.all()

    # Create exports directory
    export_dir = Path("exports")
    export_dir.mkdir(exist_ok=True)

    # Generate filename with timestamp
    filename = f"customers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = export_dir / filename

    try:
        excel_export_service.export_customers(customers, str(filepath))

        return FileResponse(
            path=str(filepath),
            filename=filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        logger.error(f"Error exporting customers: {e}")
        raise HTTPException(status_code=500, detail="Error exporting customers to Excel")


@app.get("/api/exports/commissions", tags=["Exports"])
def export_commissions_to_excel(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Export commissions to Excel file"""
    from models import Customer
    from export_service import excel_export_service

    query = db.query(Commission)

    # RBAC: Employees see only their customers' commissions
    if current_user.role == UserRole.EMPLOYEE:
        customer_ids = db.query(Customer.id).filter(
            Customer.relationship_manager_id == current_user.id
        ).all()
        customer_ids = [cid[0] for cid in customer_ids]
        query = query.filter(Commission.customer_id.in_(customer_ids))

    # Apply filters
    if start_date:
        query = query.filter(Commission.earned_date >= datetime.strptime(start_date, "%Y-%m-%d").date())
    if end_date:
        query = query.filter(Commission.earned_date <= datetime.strptime(end_date, "%Y-%m-%d").date())

    commissions = query.all()

    # Create exports directory
    export_dir = Path("exports")
    export_dir.mkdir(exist_ok=True)

    # Generate filename with timestamp
    filename = f"commissions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = export_dir / filename

    try:
        excel_export_service.export_commissions(commissions, str(filepath))

        return FileResponse(
            path=str(filepath),
            filename=filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        logger.error(f"Error exporting commissions: {e}")
        raise HTTPException(status_code=500, detail="Error exporting commissions to Excel")


@app.get("/api/exports/invoices", tags=["Exports"])
def export_invoices_to_excel(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[InvoiceStatus] = None,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Export invoices to Excel file"""
    from models import Customer
    from export_service import excel_export_service

    query = db.query(Invoice)

    # RBAC: Employees see only their customers' invoices
    if current_user.role == UserRole.EMPLOYEE:
        customer_ids = db.query(Customer.id).filter(
            Customer.relationship_manager_id == current_user.id
        ).all()
        customer_ids = [cid[0] for cid in customer_ids]
        query = query.filter(Invoice.customer_id.in_(customer_ids))

    # Apply filters
    if start_date:
        query = query.filter(Invoice.invoice_date >= datetime.strptime(start_date, "%Y-%m-%d").date())
    if end_date:
        query = query.filter(Invoice.invoice_date <= datetime.strptime(end_date, "%Y-%m-%d").date())
    if status:
        query = query.filter(Invoice.status == status)

    invoices = query.all()

    # Create exports directory
    export_dir = Path("exports")
    export_dir.mkdir(exist_ok=True)

    # Generate filename with timestamp
    filename = f"invoices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = export_dir / filename

    try:
        excel_export_service.export_invoices(invoices, str(filepath))

        return FileResponse(
            path=str(filepath),
            filename=filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        logger.error(f"Error exporting invoices: {e}")
        raise HTTPException(status_code=500, detail="Error exporting invoices to Excel")


@app.get("/api/exports/investments", tags=["Exports"])
def export_investments_to_excel(
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Export investments to Excel file"""
    from models import Customer, Investment
    from export_service import excel_export_service

    query = db.query(Investment).join(Customer, Customer.id == Investment.customer_id)

    # RBAC: Employees see only their customers' investments
    if current_user.role == UserRole.EMPLOYEE:
        query = query.filter(Customer.relationship_manager_id == current_user.id)

    investments = query.all()

    # Create exports directory
    export_dir = Path("exports")
    export_dir.mkdir(exist_ok=True)

    # Generate filename with timestamp
    filename = f"investments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = export_dir / filename

    try:
        excel_export_service.export_investments(investments, str(filepath))

        return FileResponse(
            path=str(filepath),
            filename=filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        logger.error(f"Error exporting investments: {e}")
        raise HTTPException(status_code=500, detail="Error exporting investments to Excel")

# ============================================================================
# WEB TEMPLATES / FRONTEND ROUTES
# ============================================================================

@app.get("/", response_class=HTMLResponse, tags=["Frontend"])
async def root(request: Request):
    """Root route - redirect to login or dashboard"""
    return templates.TemplateResponse("auth/login.html", {"request": request})

@app.get("/login", response_class=HTMLResponse, tags=["Frontend"])
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("auth/login.html", {"request": request})

@app.get("/change-password", response_class=HTMLResponse, tags=["Frontend"])
async def change_password_page(request: Request):
    """Change password page (for temp passwords)"""
    return templates.TemplateResponse("auth/change_password.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse, tags=["Frontend"])
async def dashboard_page(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard/index.html", {"request": request})

@app.get("/customers", response_class=HTMLResponse, tags=["Frontend"])
async def customers_list_page(request: Request):
    """Customers list page"""
    return templates.TemplateResponse("customers/list.html", {"request": request})

@app.get("/customers/{customer_id}", response_class=HTMLResponse, tags=["Frontend"])
async def customer_detail_page(request: Request, customer_id: int):
    """Customer detail page"""
    return templates.TemplateResponse("customers/detail.html", {"request": request, "customer_id": customer_id})

@app.get("/customers/create", response_class=HTMLResponse, tags=["Frontend"])
async def customer_create_page(request: Request):
    """Create customer page"""
    return templates.TemplateResponse("customers/create.html", {"request": request})

@app.get("/customers/{customer_id}/edit", response_class=HTMLResponse, tags=["Frontend"])
async def customer_edit_page(request: Request, customer_id: int):
    """Edit customer page"""
    return templates.TemplateResponse("customers/edit.html", {"request": request, "customer_id": customer_id})

@app.get("/calendar", response_class=HTMLResponse, tags=["Frontend"])
async def calendar_page(request: Request):
    """Calendar and events page"""
    return templates.TemplateResponse("calendar/index.html", {"request": request})

@app.get("/documents", response_class=HTMLResponse, tags=["Frontend"])
async def documents_page(request: Request):
    """Documents management page"""
    return templates.TemplateResponse("documents/index.html", {"request": request})

@app.get("/prospects", response_class=HTMLResponse, tags=["Frontend"])
async def prospects_list_page(request: Request):
    """Prospects list page (Admin only)"""
    return templates.TemplateResponse("prospects/list.html", {"request": request})

@app.get("/prospects/import", response_class=HTMLResponse, tags=["Frontend"])
async def prospects_import_page(request: Request):
    """Prospects import page (Admin only)"""
    return templates.TemplateResponse("prospects/import.html", {"request": request})

@app.get("/prospects/analytics", response_class=HTMLResponse, tags=["Frontend"])
async def prospects_analytics_page(request: Request):
    """Prospects analytics page (Admin only)"""
    return templates.TemplateResponse("prospects/analytics.html", {"request": request})

@app.get("/prospects/{prospect_id}", response_class=HTMLResponse, tags=["Frontend"])
async def prospect_detail_page(request: Request, prospect_id: int):
    """Prospect detail page (Admin only)"""
    return templates.TemplateResponse("prospects/detail.html", {"request": request, "prospect_id": prospect_id})

@app.get("/questionnaire-invites", response_class=HTMLResponse, tags=["Frontend"])
async def questionnaire_invites_page(request: Request):
    """Questionnaire invites management page (Admin only)"""
    return templates.TemplateResponse("questionnaire/invites.html", {"request": request})

@app.get("/questionnaire-responses", response_class=HTMLResponse, tags=["Frontend"])
async def questionnaire_responses_page(request: Request):
    """View questionnaire responses (Admin only)"""
    return templates.TemplateResponse("questionnaire/responses.html", {"request": request})

@app.get("/questionnaire/{token}", response_class=HTMLResponse, tags=["Frontend"])
async def public_questionnaire_page(request: Request, token: str):
    """Public questionnaire form (No auth required)"""
    return templates.TemplateResponse("questionnaire/public_form.html", {"request": request, "token": token})

@app.get("/portfolio/presentation", response_class=HTMLResponse, tags=["Frontend"])
async def portfolio_presentation_page(request: Request):
    """Interactive portfolio presentation dashboard (Admin only)"""
    return templates.TemplateResponse("portfolio/presentation.html", {"request": request})

@app.get("/billing/commissions", response_class=HTMLResponse, tags=["Frontend"])
async def commissions_page(request: Request):
    """Commissions page"""
    return templates.TemplateResponse("billing/commissions.html", {"request": request})

@app.get("/billing/invoices", response_class=HTMLResponse, tags=["Frontend"])
async def invoices_page(request: Request):
    """Invoices page"""
    return templates.TemplateResponse("billing/invoices.html", {"request": request})

@app.get("/reports", response_class=HTMLResponse, tags=["Frontend"])
async def reports_page(request: Request):
    """Reports and analytics page"""
    return templates.TemplateResponse("reports/index.html", {"request": request})

@app.get("/users", response_class=HTMLResponse, tags=["Frontend"])
async def users_page(request: Request):
    """User management page (Admin only)"""
    return templates.TemplateResponse("users/index.html", {"request": request})

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
