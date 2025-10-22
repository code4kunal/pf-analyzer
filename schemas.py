from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime, date
from typing import Optional, List
from models import (
    UserRole, CustomerStatus, RiskProfile, InvestmentType,
    EventType, CommunicationType, DocumentCategory,
    NotificationType, InvoiceStatus, Gender
)

# ============================================================================
# AUTHENTICATION & TOKEN SCHEMAS
# ============================================================================

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"
    is_temp_password: bool

class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)

    @validator('new_password')
    def validate_password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class PasswordResetRequest(BaseModel):
    new_password: str = Field(..., min_length=8)

# ============================================================================
# USER SCHEMAS
# ============================================================================

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    phone: Optional[str] = None

class UserCreate(UserBase):
    role: UserRole = UserRole.EMPLOYEE

class UserInvite(UserBase):
    role: UserRole = UserRole.EMPLOYEE

class UserInviteResponse(BaseModel):
    user: UserResponse
    temporary_password: str
    message: str = "User invited successfully. Please share these credentials securely."

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    phone: Optional[str]
    is_active: bool
    is_temp_password: bool
    last_login: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

class UserListResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# ============================================================================
# CUSTOMER SCHEMAS
# ============================================================================

class FamilyMemberBase(BaseModel):
    full_name: str
    relation: str
    date_of_birth: Optional[date] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None

class FamilyMemberCreate(FamilyMemberBase):
    pass

class FamilyMemberResponse(FamilyMemberBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class NomineeBase(BaseModel):
    full_name: str
    relation: str
    date_of_birth: Optional[date] = None
    percentage_share: float = Field(default=100, ge=0, le=100)

class NomineeCreate(NomineeBase):
    pass

class NomineeResponse(NomineeBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class CustomerBase(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    alternate_phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    pan_number: Optional[str] = None
    aadhar_number: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    country: str = "India"
    annual_income: Optional[float] = None
    risk_profile: Optional[RiskProfile] = None
    investment_goals: Optional[str] = None
    relationship_manager_id: Optional[int] = None
    status: CustomerStatus = CustomerStatus.PROSPECTIVE
    referral_source: Optional[str] = None
    anniversary_date: Optional[date] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    alternate_phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    pan_number: Optional[str] = None
    aadhar_number: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    country: Optional[str] = None
    annual_income: Optional[float] = None
    risk_profile: Optional[RiskProfile] = None
    investment_goals: Optional[str] = None
    relationship_manager_id: Optional[int] = None
    status: Optional[CustomerStatus] = None
    referral_source: Optional[str] = None
    anniversary_date: Optional[date] = None
    current_portfolio_value: Optional[float] = None

class CustomerResponse(CustomerBase):
    id: int
    current_portfolio_value: float
    created_at: datetime
    updated_at: Optional[datetime]
    relationship_manager: Optional[UserListResponse]

    class Config:
        from_attributes = True

class CustomerListResponse(BaseModel):
    id: int
    full_name: str
    email: str
    phone: str
    status: CustomerStatus
    current_portfolio_value: float
    relationship_manager: Optional[UserListResponse]
    created_at: datetime

    class Config:
        from_attributes = True

class CustomerDetailResponse(CustomerResponse):
    family_members: List[FamilyMemberResponse] = []
    nominees: List[NomineeResponse] = []

    class Config:
        from_attributes = True

# ============================================================================
# INVESTMENT SCHEMAS
# ============================================================================

class InvestmentBase(BaseModel):
    investment_type: InvestmentType
    investment_name: str
    description: Optional[str] = None
    invested_amount: float = Field(..., gt=0)
    current_value: Optional[float] = None
    units: Optional[float] = None
    investment_date: date
    maturity_date: Optional[date] = None

class InvestmentCreate(InvestmentBase):
    customer_id: int

class InvestmentUpdate(BaseModel):
    investment_name: Optional[str] = None
    description: Optional[str] = None
    current_value: Optional[float] = None
    units: Optional[float] = None
    maturity_date: Optional[date] = None
    is_active: Optional[bool] = None

class InvestmentResponse(InvestmentBase):
    id: int
    customer_id: int
    returns_absolute: Optional[float]
    returns_percentage: Optional[float]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# ============================================================================
# EVENT SCHEMAS
# ============================================================================

class EventBase(BaseModel):
    title: str
    event_type: EventType
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None

class EventCreate(EventBase):
    participant_ids: List[int] = []  # Customer IDs
    create_meet_link: bool = False

class EventUpdate(BaseModel):
    title: Optional[str] = None
    event_type: Optional[EventType] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    is_completed: Optional[bool] = None
    participant_ids: Optional[List[int]] = None

class EventResponse(EventBase):
    id: int
    meet_link: Optional[str]
    is_completed: bool
    created_at: datetime
    created_by: UserListResponse
    participants: List[CustomerListResponse] = []

    class Config:
        from_attributes = True

# ============================================================================
# COMMUNICATION SCHEMAS
# ============================================================================

class CommunicationBase(BaseModel):
    communication_type: CommunicationType
    subject: Optional[str] = None
    content: str
    duration_minutes: Optional[int] = None
    communication_date: datetime

class CommunicationCreate(CommunicationBase):
    customer_id: int

class CommunicationResponse(CommunicationBase):
    id: int
    customer_id: int
    user: UserListResponse
    created_at: datetime

    class Config:
        from_attributes = True

# ============================================================================
# NOTE SCHEMAS
# ============================================================================

class NoteBase(BaseModel):
    title: Optional[str] = None
    content: str
    is_private: bool = False

class NoteCreate(NoteBase):
    customer_id: int

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    is_private: Optional[bool] = None

class NoteResponse(NoteBase):
    id: int
    customer_id: int
    created_by: UserListResponse
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# ============================================================================
# COMMISSION SCHEMAS
# ============================================================================

class CommissionBase(BaseModel):
    commission_type: str
    amount: float = Field(..., gt=0)
    percentage: Optional[float] = None
    earned_date: date
    payment_date: Optional[date] = None
    is_paid: bool = False
    notes: Optional[str] = None

class CommissionCreate(CommissionBase):
    customer_id: int
    investment_id: Optional[int] = None

class CommissionUpdate(BaseModel):
    payment_date: Optional[date] = None
    is_paid: Optional[bool] = None
    notes: Optional[str] = None

class CommissionResponse(CommissionBase):
    id: int
    customer_id: int
    investment_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True

# ============================================================================
# INVOICE SCHEMAS
# ============================================================================

class InvoiceLineItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    amount: float

class InvoiceBase(BaseModel):
    invoice_date: date
    due_date: date
    subtotal: float = Field(..., ge=0)
    tax_amount: float = Field(default=0, ge=0)
    total_amount: float = Field(..., gt=0)
    notes: Optional[str] = None
    line_items: Optional[List[InvoiceLineItem]] = None

class InvoiceCreate(InvoiceBase):
    customer_id: int

class InvoiceUpdate(BaseModel):
    status: Optional[InvoiceStatus] = None
    paid_amount: Optional[float] = None
    payment_date: Optional[date] = None
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    notes: Optional[str] = None

class InvoiceResponse(InvoiceBase):
    id: int
    customer_id: int
    invoice_number: str
    status: InvoiceStatus
    paid_amount: float
    payment_date: Optional[date]
    payment_method: Optional[str]
    payment_reference: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# ============================================================================
# DOCUMENT SCHEMAS
# ============================================================================

class DocumentBase(BaseModel):
    document_name: str
    document_category: DocumentCategory
    description: Optional[str] = None

class DocumentCreate(DocumentBase):
    customer_id: int

class DocumentResponse(DocumentBase):
    id: int
    customer_id: int
    file_path: str
    file_size: Optional[int]
    mime_type: Optional[str]
    storage_type: str
    version: int
    uploaded_at: datetime

    class Config:
        from_attributes = True

# ============================================================================
# NOTIFICATION SCHEMAS
# ============================================================================

class NotificationResponse(BaseModel):
    id: int
    notification_type: NotificationType
    title: str
    message: str
    is_read: bool
    action_url: Optional[str]
    created_at: datetime
    read_at: Optional[datetime]

    class Config:
        from_attributes = True

class NotificationUpdate(BaseModel):
    is_read: bool = True

# ============================================================================
# ACTIVITY LOG SCHEMAS
# ============================================================================

class ActivityLogResponse(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    action: str
    description: str
    created_at: datetime

    class Config:
        from_attributes = True

# ============================================================================
# PAGINATION & FILTERS
# ============================================================================

class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

class CustomerFilter(BaseModel):
    search: Optional[str] = None  # Search in name, email, phone, PAN
    status: Optional[CustomerStatus] = None
    risk_profile: Optional[RiskProfile] = None
    relationship_manager_id: Optional[int] = None
    created_from: Optional[date] = None
    created_to: Optional[date] = None

class PaginatedResponse(BaseModel):
    items: List
    total: int
    page: int
    page_size: int
    total_pages: int
