from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime, date
from typing import Optional, List
from models import (
    UserRole, CustomerStatus, InvestmentType,
    EventType, CommunicationType, DocumentCategory,
    NotificationType, InvoiceStatus, Gender,
    ProspectStatus, ProspectPriority, ProspectSource,
    ProductType, GoalType, PlanStatus, RiskCategory,
    QuestionnaireInviteStatus
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

class UserInviteResponse(BaseModel):
    user: UserResponse
    temporary_password: str
    message: str = "User invited successfully. Please share these credentials securely."

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    is_temp_password: bool

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
    risk_profile: Optional[RiskCategory] = None
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
    risk_profile: Optional[RiskCategory] = None
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

# ============================================================================
# PROSPECT SCHEMAS
# ============================================================================

class ProspectBase(BaseModel):
    full_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    alternate_phone: Optional[str] = None
    company: Optional[str] = None
    designation: Optional[str] = None
    status: ProspectStatus = ProspectStatus.NEW
    priority: ProspectPriority = ProspectPriority.WARM
    estimated_portfolio_value: Optional[float] = None
    interested_services: Optional[List[str]] = None
    source: ProspectSource = ProspectSource.MANUAL
    referral_source: Optional[str] = None
    assigned_to_id: Optional[int] = None
    next_follow_up_date: Optional[datetime] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None

class ProspectCreate(ProspectBase):
    pass

class ProspectUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    alternate_phone: Optional[str] = None
    company: Optional[str] = None
    designation: Optional[str] = None
    status: Optional[ProspectStatus] = None
    priority: Optional[ProspectPriority] = None
    estimated_portfolio_value: Optional[float] = None
    interested_services: Optional[List[str]] = None
    referral_source: Optional[str] = None
    assigned_to_id: Optional[int] = None
    next_follow_up_date: Optional[datetime] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None

class ProspectResponse(ProspectBase):
    id: int
    import_batch_id: Optional[str]
    import_file_name: Optional[str]
    import_date: Optional[datetime]
    converted_to_customer_id: Optional[int]
    converted_at: Optional[datetime]
    first_contact_date: Optional[datetime]
    last_contact_date: Optional[datetime]
    contact_attempts: int
    custom_fields: Optional[dict] = None
    created_at: datetime
    updated_at: Optional[datetime]
    assigned_to: Optional[UserListResponse]
    created_by: Optional[UserListResponse]
    converted_by: Optional[UserListResponse]

    class Config:
        from_attributes = True

class ProspectListResponse(BaseModel):
    id: int
    full_name: str
    email: Optional[str]
    phone: Optional[str]
    company: Optional[str]
    status: ProspectStatus
    priority: ProspectPriority
    source: ProspectSource
    estimated_portfolio_value: Optional[float]
    next_follow_up_date: Optional[datetime]
    assigned_to: Optional[UserListResponse]
    created_at: datetime

    class Config:
        from_attributes = True

class ProspectDetailResponse(ProspectResponse):
    communications: List['ProspectCommunicationResponse'] = []
    activities: List['ProspectActivityResponse'] = []

    class Config:
        from_attributes = True

class ProspectCommunicationBase(BaseModel):
    communication_type: CommunicationType
    subject: Optional[str] = None
    content: str
    duration_minutes: Optional[int] = None
    communication_date: datetime

class ProspectCommunicationCreate(ProspectCommunicationBase):
    prospect_id: int

class ProspectCommunicationResponse(ProspectCommunicationBase):
    id: int
    prospect_id: int
    user: UserListResponse
    created_at: datetime

    class Config:
        from_attributes = True

class ProspectActivityResponse(BaseModel):
    id: int
    action: str
    description: str
    changes: Optional[dict]
    created_at: datetime
    user: Optional[UserListResponse]

    class Config:
        from_attributes = True

class ProspectConversionRequest(BaseModel):
    relationship_manager_id: Optional[int] = None
    copy_notes: bool = True

# ============================================================================
# IMPORT SCHEMAS
# ============================================================================

class ImportPreviewRow(BaseModel):
    row_number: int
    data: dict
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    is_duplicate: bool = False
    duplicate_info: Optional[dict] = None

class ImportMappingRequest(BaseModel):
    file_key: str  # Temporary file identifier
    column_mappings: dict  # {csv_column: prospect_field}

class ImportPreviewResponse(BaseModel):
    file_key: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    suggested_mappings: dict
    preview_rows: List[ImportPreviewRow]

class ImportConfirmRequest(BaseModel):
    file_key: str
    column_mappings: dict
    skip_duplicates: bool = True

class ImportResultResponse(BaseModel):
    batch_id: str
    total_records: int
    successful_imports: int
    failed_imports: int
    errors: List[dict] = []
    message: str

class ImportBatchResponse(BaseModel):
    id: int
    batch_id: str
    file_name: str
    file_size: Optional[int]
    total_records: int
    successful_imports: int
    failed_imports: int
    errors: Optional[List[dict]]
    imported_by: UserListResponse
    created_at: datetime

    class Config:
        from_attributes = True

# ============================================================================
# PROSPECT FILTER SCHEMAS
# ============================================================================

class ProspectFilter(BaseModel):
    search: Optional[str] = None  # Search in name, email, phone, company
    status: Optional[List[ProspectStatus]] = None
    priority: Optional[List[ProspectPriority]] = None
    source: Optional[List[ProspectSource]] = None
    assigned_to_id: Optional[int] = None
    created_from: Optional[date] = None
    created_to: Optional[date] = None
    next_followup_from: Optional[date] = None
    next_followup_to: Optional[date] = None
    estimated_value_min: Optional[float] = None
    estimated_value_max: Optional[float] = None
    tags: Optional[List[str]] = None
    is_converted: Optional[bool] = None

# ============================================================================
# ANALYTICS SCHEMAS
# ============================================================================

class ProspectAnalyticsFunnelResponse(BaseModel):
    status: ProspectStatus
    count: int
    percentage: float

class ProspectAnalyticsSourceResponse(BaseModel):
    source: ProspectSource
    count: int
    percentage: float
    conversion_rate: Optional[float] = None

class ProspectAnalyticsResponse(BaseModel):
    total_prospects: int
    by_status: List[ProspectAnalyticsFunnelResponse]
    by_source: List[ProspectAnalyticsSourceResponse]
    by_priority: dict
    conversion_stats: dict
    avg_time_to_convert_days: Optional[float] = None
    total_converted: int
    conversion_rate: float

# ============================================================================
# BULK OPERATIONS
# ============================================================================

class BulkUpdateRequest(BaseModel):
    prospect_ids: List[int]
    updates: ProspectUpdate

class BulkDeleteRequest(BaseModel):
    prospect_ids: List[int]

class BulkAssignRequest(BaseModel):
    prospect_ids: List[int]
    assigned_to_id: int

# ============================================================================
# FINANCIAL PLANNING SCHEMAS
# ============================================================================

# -------- FINANCIAL PRODUCT SCHEMAS --------

class FinancialProductBase(BaseModel):
    product_type: ProductType
    product_code: str = Field(..., description="ISIN/NSE Symbol/Fund Code")
    product_name: str

    # For Stocks
    exchange: Optional[str] = None
    sector: Optional[str] = None
    market_cap_category: Optional[str] = None  # Large/Mid/Small
    price: Optional[float] = None
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None

    # For Mutual Funds
    fund_house: Optional[str] = None
    category: Optional[str] = None  # Large Cap, Mid Cap, Debt, etc.
    sub_category: Optional[str] = None
    nav: Optional[float] = None
    aum: Optional[float] = None  # Assets Under Management
    expense_ratio: Optional[float] = None
    exit_load: Optional[float] = None
    min_investment: Optional[float] = None
    min_sip: Optional[float] = None

    # Performance Metrics
    return_1m: Optional[float] = None
    return_3m: Optional[float] = None
    return_6m: Optional[float] = None
    return_1y: Optional[float] = None
    return_3y: Optional[float] = None
    return_5y: Optional[float] = None

    # Risk Metrics
    beta: Optional[float] = None
    alpha: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    standard_deviation: Optional[float] = None

    is_active: Optional[bool] = True

class FinancialProductCreate(FinancialProductBase):
    pass

class FinancialProductUpdate(BaseModel):
    product_name: Optional[str] = None
    price: Optional[float] = None
    nav: Optional[float] = None
    return_1m: Optional[float] = None
    return_3m: Optional[float] = None
    return_6m: Optional[float] = None
    return_1y: Optional[float] = None
    return_3y: Optional[float] = None
    return_5y: Optional[float] = None
    beta: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    is_active: Optional[bool] = None

class FinancialProductResponse(FinancialProductBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# -------- FINANCIAL GOAL SCHEMAS --------

class FinancialGoalBase(BaseModel):
    goal_type: GoalType
    goal_name: str
    target_amount: float = Field(..., gt=0)
    years_to_goal: int = Field(..., gt=0, le=50)
    current_savings: Optional[float] = Field(0, ge=0)
    inflation_rate: Optional[float] = Field(6.0, ge=0, le=20)  # Default 6% for India
    expected_return: Optional[float] = Field(12.0, ge=0, le=30)  # Default 12%
    priority: Optional[str] = Field("MEDIUM", description="HIGH, MEDIUM, LOW")
    notes: Optional[str] = None

class FinancialGoalCreate(FinancialGoalBase):
    plan_id: int

class FinancialGoalUpdate(BaseModel):
    goal_name: Optional[str] = None
    target_amount: Optional[float] = Field(None, gt=0)
    years_to_goal: Optional[int] = Field(None, gt=0, le=50)
    current_savings: Optional[float] = Field(None, ge=0)
    inflation_rate: Optional[float] = Field(None, ge=0, le=20)
    expected_return: Optional[float] = Field(None, ge=0, le=30)
    priority: Optional[str] = None
    notes: Optional[str] = None

class FinancialGoalResponse(FinancialGoalBase):
    id: int
    plan_id: int
    inflation_adjusted_target: Optional[float] = None
    required_monthly_sip: Optional[float] = None
    required_lumpsum: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True

# -------- PORTFOLIO COMPONENT SCHEMAS --------

class PortfolioComponentBase(BaseModel):
    product_id: int
    allocation_percentage: float = Field(..., ge=0, le=100)
    investment_type: InvestmentType = InvestmentType.BOTH
    sip_amount: Optional[float] = Field(0, ge=0)
    lumpsum_amount: Optional[float] = Field(0, ge=0)
    notes: Optional[str] = None

class PortfolioComponentCreate(PortfolioComponentBase):
    plan_id: int

class PortfolioComponentUpdate(BaseModel):
    allocation_percentage: Optional[float] = Field(None, ge=0, le=100)
    investment_type: Optional[InvestmentType] = None
    sip_amount: Optional[float] = Field(None, ge=0)
    lumpsum_amount: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None

class PortfolioComponentResponse(PortfolioComponentBase):
    id: int
    plan_id: int
    projected_value_1y: Optional[float] = None
    projected_value_3y: Optional[float] = None
    projected_value_5y: Optional[float] = None
    created_at: datetime

    # Nested product details
    product: Optional[FinancialProductResponse] = None

    class Config:
        from_attributes = True

# -------- RISK PROFILE SCHEMAS --------

class RiskProfileQuestionAnswer(BaseModel):
    question_id: str
    question_text: str
    answer: str
    score: int

class RiskProfileBase(BaseModel):
    total_score: int
    risk_category: RiskCategory
    questionnaire_version: Optional[str] = "1.0"
    responses: Optional[List[RiskProfileQuestionAnswer]] = []

class RiskProfileCreate(RiskProfileBase):
    customer_id: int

class RiskProfileResponse(RiskProfileBase):
    id: int
    customer_id: int
    recommended_equity_allocation: Optional[int] = None
    recommended_debt_allocation: Optional[int] = None
    recommended_gold_allocation: Optional[int] = None
    completed_at: datetime

    class Config:
        from_attributes = True

# -------- FINANCIAL PLAN SCHEMAS --------

class FinancialPlanBase(BaseModel):
    plan_name: str
    description: Optional[str] = None
    risk_category: Optional[RiskCategory] = None

    # Client Profile
    current_age: Optional[int] = Field(None, ge=18, le=100)
    retirement_age: Optional[int] = Field(None, ge=40, le=80)
    monthly_income: Optional[float] = Field(None, ge=0)
    monthly_expenses: Optional[float] = Field(None, ge=0)
    existing_investments: Optional[float] = Field(None, ge=0)
    existing_liabilities: Optional[float] = Field(None, ge=0)

    # Recommended Asset Allocation (%)
    recommended_equity: Optional[float] = Field(None, ge=0, le=100)
    recommended_debt: Optional[float] = Field(None, ge=0, le=100)
    recommended_gold: Optional[float] = Field(None, ge=0, le=100)
    recommended_alternative: Optional[float] = Field(None, ge=0, le=100)

    # Investment Capacity
    total_investment_amount: Optional[float] = Field(None, ge=0)
    monthly_sip_capacity: Optional[float] = Field(None, ge=0)

    notes: Optional[str] = None
    status: Optional[PlanStatus] = PlanStatus.DRAFT

class FinancialPlanCreate(FinancialPlanBase):
    customer_id: int

class FinancialPlanUpdate(BaseModel):
    plan_name: Optional[str] = None
    description: Optional[str] = None
    risk_category: Optional[RiskCategory] = None
    current_age: Optional[int] = Field(None, ge=18, le=100)
    retirement_age: Optional[int] = Field(None, ge=40, le=80)
    monthly_income: Optional[float] = Field(None, ge=0)
    monthly_expenses: Optional[float] = Field(None, ge=0)
    existing_investments: Optional[float] = Field(None, ge=0)
    existing_liabilities: Optional[float] = Field(None, ge=0)
    recommended_equity: Optional[float] = Field(None, ge=0, le=100)
    recommended_debt: Optional[float] = Field(None, ge=0, le=100)
    recommended_gold: Optional[float] = Field(None, ge=0, le=100)
    recommended_alternative: Optional[float] = Field(None, ge=0, le=100)
    total_investment_amount: Optional[float] = Field(None, ge=0)
    monthly_sip_capacity: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None
    status: Optional[PlanStatus] = None

class FinancialPlanResponse(FinancialPlanBase):
    id: int
    customer_id: int
    created_by_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    # Nested data
    goals: Optional[List[FinancialGoalResponse]] = []
    portfolio_components: Optional[List[PortfolioComponentResponse]] = []

    class Config:
        from_attributes = True

class FinancialPlanSummary(BaseModel):
    """Lightweight plan summary for listings"""
    id: int
    customer_id: int
    plan_name: str
    status: PlanStatus
    risk_category: Optional[RiskCategory] = None
    total_investment_amount: Optional[float] = None
    created_at: datetime
    goals_count: int = 0
    portfolio_components_count: int = 0

    class Config:
        from_attributes = True

# -------- BENCHMARK SCHEMAS --------

class BenchmarkBase(BaseModel):
    benchmark_name: str
    benchmark_code: str
    category: Optional[str] = None
    description: Optional[str] = None
    current_value: Optional[float] = None
    return_1m: Optional[float] = None
    return_3m: Optional[float] = None
    return_6m: Optional[float] = None
    return_1y: Optional[float] = None
    return_3y: Optional[float] = None
    return_5y: Optional[float] = None
    standard_deviation: Optional[float] = None

class BenchmarkCreate(BenchmarkBase):
    pass

class BenchmarkUpdate(BaseModel):
    current_value: Optional[float] = None
    return_1m: Optional[float] = None
    return_3m: Optional[float] = None
    return_6m: Optional[float] = None
    return_1y: Optional[float] = None
    return_3y: Optional[float] = None
    return_5y: Optional[float] = None
    standard_deviation: Optional[float] = None

class BenchmarkResponse(BenchmarkBase):
    id: int
    last_updated: datetime

    class Config:
        from_attributes = True

# -------- MODEL PORTFOLIO SCHEMAS --------

class ModelPortfolioComponent(BaseModel):
    product_id: int
    allocation_percentage: float = Field(..., ge=0, le=100)

class ModelPortfolioBase(BaseModel):
    portfolio_name: str
    portfolio_type: str  # Thematic, Smart Beta, Conservative, etc.
    description: Optional[str] = None
    risk_category: Optional[RiskCategory] = None
    min_investment: Optional[float] = None
    expected_return: Optional[float] = None
    historical_return_1y: Optional[float] = None
    historical_return_3y: Optional[float] = None
    components: List[ModelPortfolioComponent]
    is_active: Optional[bool] = True

class ModelPortfolioCreate(ModelPortfolioBase):
    pass

class ModelPortfolioUpdate(BaseModel):
    portfolio_name: Optional[str] = None
    portfolio_type: Optional[str] = None
    description: Optional[str] = None
    risk_category: Optional[RiskCategory] = None
    min_investment: Optional[float] = None
    expected_return: Optional[float] = None
    components: Optional[List[ModelPortfolioComponent]] = None
    is_active: Optional[bool] = None

class ModelPortfolioResponse(ModelPortfolioBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# -------- PORTFOLIO ANALYSIS SCHEMAS --------

class PortfolioAnalysisRequest(BaseModel):
    """Request for portfolio performance analysis"""
    plan_id: int
    years: int = Field(default=5, ge=1, le=30)
    monte_carlo_simulations: Optional[int] = Field(1000, ge=100, le=10000)

class PortfolioPerformanceProjection(BaseModel):
    """Portfolio performance projection"""
    year: int
    expected_value: float
    conservative_value: float  # Lower bound (25th percentile)
    optimistic_value: float    # Upper bound (75th percentile)

class AssetAllocationBreakdown(BaseModel):
    """Asset class allocation breakdown"""
    equity: float
    debt: float
    gold: float
    alternative: float

class PortfolioAnalysisResponse(BaseModel):
    """Complete portfolio analysis response"""
    plan_id: int
    total_investment: float
    expected_return_percentage: float
    portfolio_beta: Optional[float] = None
    portfolio_alpha: Optional[float] = None
    sharpe_ratio: Optional[float] = None

    asset_allocation: AssetAllocationBreakdown
    projections: List[PortfolioPerformanceProjection]

    # Benchmark comparison
    benchmark_name: Optional[str] = None
    outperformance: Optional[float] = None  # % vs benchmark

# ============================================================================
# CLIENT PROFILING QUESTIONNAIRE SCHEMAS
# ============================================================================

# -------- QUESTIONNAIRE INVITE SCHEMAS --------

class QuestionnaireInviteCreate(BaseModel):
    recipient_name: str = Field(..., min_length=2, max_length=100)
    recipient_email: EmailStr
    recipient_phone: Optional[str] = None
    expires_in_days: Optional[int] = Field(7, ge=1, le=90)  # Default 7 days
    auto_create_prospect: Optional[bool] = True
    notes: Optional[str] = None
    custom_message: Optional[str] = None

class QuestionnaireInviteResponse(BaseModel):
    id: int
    invite_token: str
    recipient_name: str
    recipient_email: str
    recipient_phone: Optional[str] = None
    status: QuestionnaireInviteStatus
    created_by_id: int
    sent_at: datetime
    expires_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    auto_create_prospect: bool
    created_prospect_id: Optional[int] = None
    notes: Optional[str] = None
    custom_message: Optional[str] = None

    # Computed fields
    invite_url: Optional[str] = None
    is_expired: Optional[bool] = False

    class Config:
        from_attributes = True

class QuestionnaireInviteListResponse(BaseModel):
    id: int
    recipient_name: str
    recipient_email: str
    status: QuestionnaireInviteStatus
    sent_at: datetime
    expires_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_prospect_id: Optional[int] = None
    is_expired: bool = False

    class Config:
        from_attributes = True

# -------- CLIENT PROFILING RESPONSE SCHEMAS --------

class FinancialGoalInput(BaseModel):
    """Single financial goal input"""
    goal_type: GoalType
    goal_name: str
    target_amount: float = Field(..., gt=0)
    years_to_goal: int = Field(..., gt=0, le=50)
    priority: str = Field("MEDIUM", description="HIGH, MEDIUM, LOW")

class ClientProfilingSubmission(BaseModel):
    """Complete client profiling questionnaire submission"""

    # Personal Information (Mandatory)
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=10, description="Phone number is required")
    date_of_birth: Optional[date] = None
    occupation: Optional[str] = None
    annual_income: Optional[float] = Field(None, ge=0)

    # Financial Information (Optional)
    monthly_income: Optional[float] = Field(None, ge=0)
    monthly_expenses: Optional[float] = Field(None, ge=0)
    existing_investments: Optional[float] = Field(None, ge=0)
    existing_liabilities: Optional[float] = Field(None, ge=0)
    emergency_fund_months: Optional[int] = Field(None, ge=0, le=24)

    # Investment Preferences (Mandatory: timeline and capacity for portfolio creation)
    investment_experience: Optional[str] = Field(None, description="Beginner, Intermediate, Advanced")
    preferred_investment_types: Optional[List[str]] = []  # ["Equity", "Mutual Funds", "ETF", "Bonds"]
    investment_timeline: str = Field(..., description="Mandatory: Short-term (<3 years), Medium-term (3-7 years), Long-term (>7 years)")
    monthly_investment_capacity: Optional[float] = Field(None, ge=0, description="Provide at least one: SIP or Lumpsum")
    lumpsum_availability: Optional[float] = Field(None, ge=0, description="Provide at least one: SIP or Lumpsum")

    # Financial Goals (Optional)
    financial_goals: Optional[List[FinancialGoalInput]] = []

    # Risk Assessment (Mandatory - 10 questions from risk profiling service)
    risk_questionnaire_responses: List[RiskProfileQuestionAnswer]

    # Additional Information (Optional)
    current_advisor: Optional[str] = None
    how_did_you_hear: Optional[str] = None
    specific_requirements: Optional[str] = None
    preferred_contact_time: Optional[str] = None

    @validator('monthly_investment_capacity', 'lumpsum_availability')
    def validate_investment_capacity(cls, v, values):
        # Check if at least one investment capacity is provided
        if 'monthly_investment_capacity' in values and 'lumpsum_availability' in values:
            monthly = values.get('monthly_investment_capacity') or 0
            lumpsum = values.get('lumpsum_availability') or 0
            if monthly == 0 and lumpsum == 0 and v == 0:
                raise ValueError('Please provide at least one: Monthly SIP capacity or Lumpsum availability')
        return v

class ClientProfilingResponseDetail(BaseModel):
    """Detailed client profiling response"""
    id: int
    invite_id: int
    prospect_id: Optional[int] = None

    # Personal Information
    full_name: str
    email: str
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    occupation: Optional[str] = None
    annual_income: Optional[float] = None

    # Financial Information
    monthly_income: Optional[float] = None
    monthly_expenses: Optional[float] = None
    existing_investments: Optional[float] = None
    existing_liabilities: Optional[float] = None
    emergency_fund_months: Optional[int] = None

    # Investment Preferences
    investment_experience: Optional[str] = None
    preferred_investment_types: Optional[List[str]] = None
    investment_timeline: Optional[str] = None
    monthly_investment_capacity: Optional[float] = None
    lumpsum_availability: Optional[float] = None

    # Goals
    financial_goals: Optional[List[dict]] = None

    # Risk Assessment
    calculated_risk_score: Optional[int] = None
    calculated_risk_category: Optional[RiskCategory] = None

    # Additional
    current_advisor: Optional[str] = None
    how_did_you_hear: Optional[str] = None
    specific_requirements: Optional[str] = None
    preferred_contact_time: Optional[str] = None

    submitted_at: datetime

    class Config:
        from_attributes = True

# ============================================================================
# PORTFOLIO CONSTRUCTION SCHEMAS
# ============================================================================

class PortfolioGenerationRequest(BaseModel):
    """Request to generate model portfolios"""
    prospect_id: Optional[int] = None
    response_id: Optional[int] = None  # If generating from questionnaire response
    risk_profile: RiskCategory
    monthly_sip: float = Field(0, ge=0)
    lumpsum: float = Field(0, ge=0)
    timeline_years: int = Field(10, ge=1, le=50)
    step_up_percent: float = Field(10, ge=0, le=50)
    equity_preference: Optional[float] = Field(None, ge=0, le=100, description="Override equity % for adaptive dashboard")

class PortfolioAllocationBreakdown(BaseModel):
    """Breakdown of allocation"""
    percent: float
    monthly: float
    lumpsum: float

class PortfolioYearProjection(BaseModel):
    """Year-by-year projection"""
    year: int
    monthly_sip: float
    annual_invested: float
    total_invested: float
    portfolio_value: float
    gains: float
    return_percent: float

class TaxHarvestingSchedule(BaseModel):
    """Tax harvesting opportunity"""
    year: int
    portfolio_value: float
    total_gains: float
    harvest_amount: float
    tax_saved: float
    action: str
    benefit: str

class ModelPortfolioResponse(BaseModel):
    """Model portfolio with complete details"""
    name: str
    strategy: str
    risk_profile: RiskCategory
    allocation: Dict
    projections: Dict
    tax_harvesting: Dict
    parameters: Dict
    mutual_fund_schemes: Optional[Dict] = None  # Live MF data
    health_score: Optional[Dict] = None

class PortfolioComparisonResponse(BaseModel):
    """Compare multiple portfolio options"""
    portfolios: List[ModelPortfolioResponse]
    comparison_metrics: Dict
    scenario_data: Optional[Dict] = None
    rebalancing_strategy: Optional[Dict] = None
    suitability_check: Optional[Dict] = None

# -------- ANALYTICS SCHEMAS --------

class QuestionnaireAnalytics(BaseModel):
    """Analytics for questionnaire invites"""
    total_invites: int
    pending: int
    completed: int
    expired: int
    completion_rate: float
    avg_completion_time_hours: Optional[float] = None

    # Response insights
    avg_monthly_income: Optional[float] = None
    avg_investment_capacity: Optional[float] = None
    risk_category_distribution: dict = {}  # {"CONSERVATIVE": 10, "MODERATE": 20, ...}
    top_goals: List[dict] = []  # [{"goal_type": "RETIREMENT", "count": 15}, ...]
