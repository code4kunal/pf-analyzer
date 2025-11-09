from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Text, Boolean, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum
from datetime import datetime

# ============================================================================
# ENUMS
# ============================================================================

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    EMPLOYEE = "EMPLOYEE"

class CustomerStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    PROSPECTIVE = "PROSPECTIVE"

class RiskCategory(str, enum.Enum):
    CONSERVATIVE = "CONSERVATIVE"
    MODERATE = "MODERATE"
    AGGRESSIVE = "AGGRESSIVE"

class InvestmentType(str, enum.Enum):
    MUTUAL_FUND = "MUTUAL_FUND"
    STOCK = "STOCK"
    BOND = "BOND"
    INSURANCE = "INSURANCE"
    FIXED_DEPOSIT = "FIXED_DEPOSIT"
    OTHER = "OTHER"

class EventType(str, enum.Enum):
    SEMINAR = "SEMINAR"
    ONE_ON_ONE = "ONE_ON_ONE"
    GROUP_CALL = "GROUP_CALL"
    FOLLOW_UP = "FOLLOW_UP"
    REVIEW_MEETING = "REVIEW_MEETING"

class CommunicationType(str, enum.Enum):
    CALL = "CALL"
    EMAIL = "EMAIL"
    MEETING = "MEETING"
    WHATSAPP = "WHATSAPP"
    OTHER = "OTHER"

class DocumentCategory(str, enum.Enum):
    KYC = "KYC"
    AGREEMENT = "AGREEMENT"
    BANK_DETAILS = "BANK_DETAILS"
    INVESTMENT_PROOF = "INVESTMENT_PROOF"
    OTHER = "OTHER"

class NotificationType(str, enum.Enum):
    EVENT_REMINDER = "EVENT_REMINDER"
    BIRTHDAY = "BIRTHDAY"
    ANNIVERSARY = "ANNIVERSARY"
    FOLLOW_UP = "FOLLOW_UP"
    SYSTEM = "SYSTEM"

class InvoiceStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SENT = "SENT"
    PAID = "PAID"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"

class Gender(str, enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"

class ProspectStatus(str, enum.Enum):
    NEW = "NEW"
    CONTACTED = "CONTACTED"
    QUALIFIED = "QUALIFIED"
    NEGOTIATION = "NEGOTIATION"
    CONVERTED = "CONVERTED"
    LOST = "LOST"

class ProspectPriority(str, enum.Enum):
    HOT = "HOT"
    WARM = "WARM"
    COLD = "COLD"

class ProspectSource(str, enum.Enum):
    IMPORT = "IMPORT"
    MANUAL = "MANUAL"
    REFERRAL = "REFERRAL"
    WEBSITE = "WEBSITE"
    EVENT = "EVENT"
    OTHER = "OTHER"

# ============================================================================
# USER & AUTHENTICATION
# ============================================================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.EMPLOYEE)

    # Authentication
    is_active = Column(Boolean, default=True)
    is_temp_password = Column(Boolean, default=True)  # Force password change on first login
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Contact
    phone = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    created_customers = relationship("Customer", back_populates="created_by", foreign_keys="Customer.created_by_id")
    assigned_customers = relationship("Customer", back_populates="relationship_manager", foreign_keys="Customer.relationship_manager_id")
    events = relationship("Event", back_populates="created_by")
    communications = relationship("Communication", back_populates="user")
    notes = relationship("Note", back_populates="created_by")
    notifications = relationship("Notification", back_populates="user")

# ============================================================================
# CUSTOMER MANAGEMENT
# ============================================================================

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)

    # Basic Information
    full_name = Column(String, nullable=False, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=False)
    alternate_phone = Column(String, nullable=True)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(Enum(Gender), nullable=True)

    # KYC Information
    pan_number = Column(String, unique=True, index=True, nullable=True)
    aadhar_number = Column(String, nullable=True)

    # Address
    address_line1 = Column(String, nullable=True)
    address_line2 = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    pincode = Column(String, nullable=True)
    country = Column(String, default="India")

    # Financial Profile
    annual_income = Column(Float, nullable=True)
    risk_profile = Column(Enum(RiskCategory), nullable=True)
    investment_goals = Column(Text, nullable=True)
    current_portfolio_value = Column(Float, default=0)

    # Relationship Management
    relationship_manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(Enum(CustomerStatus), default=CustomerStatus.PROSPECTIVE)
    referral_source = Column(String, nullable=True)

    # Important Dates
    anniversary_date = Column(Date, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    relationship_manager = relationship("User", back_populates="assigned_customers", foreign_keys=[relationship_manager_id])
    created_by = relationship("User", back_populates="created_customers", foreign_keys=[created_by_id])
    investments = relationship("Investment", back_populates="customer", cascade="all, delete-orphan")
    family_members = relationship("FamilyMember", back_populates="customer", cascade="all, delete-orphan")
    nominees = relationship("Nominee", back_populates="customer", cascade="all, delete-orphan")
    communications = relationship("Communication", back_populates="customer", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="customer", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="customer", cascade="all, delete-orphan")
    events = relationship("Event", secondary="event_participants", back_populates="participants")
    commissions = relationship("Commission", back_populates="customer", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="customer", cascade="all, delete-orphan")

class FamilyMember(Base):
    __tablename__ = "family_members"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)

    full_name = Column(String, nullable=False)
    relation = Column(String, nullable=False)  # Spouse, Child, Parent, etc.
    date_of_birth = Column(Date, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="family_members")

class Nominee(Base):
    __tablename__ = "nominees"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)

    full_name = Column(String, nullable=False)
    relation = Column(String, nullable=False)  # Spouse, Child, Parent, etc.
    date_of_birth = Column(Date, nullable=True)
    percentage_share = Column(Float, default=100)  # Percentage of portfolio

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="nominees")

# ============================================================================
# INVESTMENT TRACKING
# ============================================================================

class Investment(Base):
    __tablename__ = "investments"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)

    # Investment Details
    investment_type = Column(Enum(InvestmentType), nullable=False)
    investment_name = Column(String, nullable=False)  # Fund name, stock symbol, etc.
    description = Column(Text, nullable=True)

    # Financial Details
    invested_amount = Column(Float, nullable=False)
    current_value = Column(Float, nullable=True)
    units = Column(Float, nullable=True)  # For MF, stocks

    # Dates
    investment_date = Column(Date, nullable=False)
    maturity_date = Column(Date, nullable=True)  # For FD, bonds

    # Performance
    returns_absolute = Column(Float, nullable=True)
    returns_percentage = Column(Float, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="investments")

# ============================================================================
# CALENDAR & EVENTS
# ============================================================================

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String, nullable=False)
    event_type = Column(Enum(EventType), nullable=False)
    description = Column(Text, nullable=True)

    # Date & Time
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=False)

    # Google Meet
    meet_link = Column(String, nullable=True)
    google_event_id = Column(String, nullable=True)  # For future sync if needed

    # Location (for in-person meetings)
    location = Column(String, nullable=True)

    # Status
    is_completed = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    created_by = relationship("User", back_populates="events")
    participants = relationship("Customer", secondary="event_participants", back_populates="events")

# Association table for Event-Customer many-to-many relationship
class EventParticipant(Base):
    __tablename__ = "event_participants"

    event_id = Column(Integer, ForeignKey("events.id"), primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# ============================================================================
# COMMUNICATION & NOTES
# ============================================================================

class Communication(Base):
    __tablename__ = "communications"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    communication_type = Column(Enum(CommunicationType), nullable=False)
    subject = Column(String, nullable=True)
    content = Column(Text, nullable=False)

    # Metadata
    duration_minutes = Column(Integer, nullable=True)  # For calls

    # Timestamps
    communication_date = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="communications")
    user = relationship("User", back_populates="communications")

class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    title = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    is_private = Column(Boolean, default=False)  # Private notes visible only to creator

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="notes")
    created_by = relationship("User", back_populates="notes")

# ============================================================================
# COMMISSION & BILLING
# ============================================================================

class Commission(Base):
    __tablename__ = "commissions"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    investment_id = Column(Integer, ForeignKey("investments.id"), nullable=True)

    # Commission Details
    commission_type = Column(String, nullable=False)  # Upfront, Trail, Advisory Fee, etc.
    amount = Column(Float, nullable=False)
    percentage = Column(Float, nullable=True)

    # Dates
    earned_date = Column(Date, nullable=False, index=True)
    payment_date = Column(Date, nullable=True)

    # Status
    is_paid = Column(Boolean, default=False)

    # Notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="commissions")

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)

    # Invoice Details
    invoice_number = Column(String, unique=True, nullable=False, index=True)
    invoice_date = Column(Date, nullable=False, index=True)
    due_date = Column(Date, nullable=False)

    # Amounts
    subtotal = Column(Float, nullable=False)
    tax_amount = Column(Float, default=0)
    total_amount = Column(Float, nullable=False)
    paid_amount = Column(Float, default=0)

    # Status
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.DRAFT)

    # Payment Details
    payment_date = Column(Date, nullable=True)
    payment_method = Column(String, nullable=True)
    payment_reference = Column(String, nullable=True)

    # Notes
    notes = Column(Text, nullable=True)

    # Line items stored as JSON
    line_items = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="invoices")

# ============================================================================
# DOCUMENT MANAGEMENT
# ============================================================================

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)

    # Document Details
    document_name = Column(String, nullable=False)
    document_category = Column(Enum(DocumentCategory), nullable=False)
    file_path = Column(String, nullable=False)  # Local path or S3 key
    file_size = Column(Integer, nullable=True)  # Size in bytes
    mime_type = Column(String, nullable=True)

    # Storage
    storage_type = Column(String, default="local")  # local or s3

    # Version Control
    version = Column(Integer, default=1)

    # Metadata
    description = Column(Text, nullable=True)

    # Timestamps
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="documents")

# ============================================================================
# NOTIFICATIONS
# ============================================================================

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Notification Details
    notification_type = Column(Enum(NotificationType), nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)

    # Status
    is_read = Column(Boolean, default=False)

    # Actions
    action_url = Column(String, nullable=True)  # Link to relevant page

    # Related entities
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="notifications")

# ============================================================================
# ACTIVITY LOG (Auto-tracked timeline)
# ============================================================================

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Activity Details
    entity_type = Column(String, nullable=False)  # customer, investment, event, etc.
    entity_id = Column(Integer, nullable=False)
    action = Column(String, nullable=False)  # created, updated, deleted, etc.
    description = Column(String, nullable=False)

    # User who performed the action
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Changes (store as JSON for flexibility)
    changes = Column(JSON, nullable=True)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

# ============================================================================
# PROSPECT MANAGEMENT
# ============================================================================

class Prospect(Base):
    __tablename__ = "prospects"

    id = Column(Integer, primary_key=True, index=True)

    # Basic Information (flexible for imports)
    full_name = Column(String, nullable=False, index=True)
    email = Column(String, nullable=True, index=True)
    phone = Column(String, nullable=True, index=True)
    alternate_phone = Column(String, nullable=True)
    company = Column(String, nullable=True, index=True)
    designation = Column(String, nullable=True)

    # Lead Qualification
    status = Column(Enum(ProspectStatus), nullable=False, default=ProspectStatus.NEW, index=True)
    priority = Column(Enum(ProspectPriority), nullable=False, default=ProspectPriority.WARM, index=True)
    estimated_portfolio_value = Column(Float, nullable=True)
    interested_services = Column(JSON, nullable=True)  # Array of services

    # Source Tracking
    source = Column(Enum(ProspectSource), nullable=False, default=ProspectSource.MANUAL, index=True)
    import_batch_id = Column(String, nullable=True, index=True)  # Links to ImportBatch
    import_file_name = Column(String, nullable=True)
    import_date = Column(DateTime(timezone=True), nullable=True)
    referral_source = Column(String, nullable=True)

    # Assignment
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    # Conversion Tracking
    converted_to_customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    converted_at = Column(DateTime(timezone=True), nullable=True)
    converted_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Contact Tracking
    first_contact_date = Column(DateTime(timezone=True), nullable=True)
    last_contact_date = Column(DateTime(timezone=True), nullable=True, index=True)
    next_follow_up_date = Column(DateTime(timezone=True), nullable=True, index=True)
    contact_attempts = Column(Integer, default=0)

    # Additional Data
    notes = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # Array of tags
    custom_fields = Column(JSON, nullable=True)  # Flexible for imported data

    # Standard Fields
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    created_by = relationship("User", foreign_keys=[created_by_id])
    converted_by = relationship("User", foreign_keys=[converted_by_id])
    converted_to_customer = relationship("Customer", foreign_keys=[converted_to_customer_id])
    communications = relationship("ProspectCommunication", back_populates="prospect", cascade="all, delete-orphan")
    activities = relationship("ProspectActivity", back_populates="prospect", cascade="all, delete-orphan")

class ProspectCommunication(Base):
    __tablename__ = "prospect_communications"

    id = Column(Integer, primary_key=True, index=True)
    prospect_id = Column(Integer, ForeignKey("prospects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    communication_type = Column(Enum(CommunicationType), nullable=False)
    subject = Column(String, nullable=True)
    content = Column(Text, nullable=False)

    # Metadata
    duration_minutes = Column(Integer, nullable=True)  # For calls

    # Timestamps
    communication_date = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    prospect = relationship("Prospect", back_populates="communications")
    user = relationship("User")

class ProspectActivity(Base):
    __tablename__ = "prospect_activities"

    id = Column(Integer, primary_key=True, index=True)
    prospect_id = Column(Integer, ForeignKey("prospects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Activity Details
    action = Column(String, nullable=False)  # STATUS_CHANGED, ASSIGNED, CONTACTED, etc.
    description = Column(String, nullable=False)
    changes = Column(JSON, nullable=True)  # Before/after values

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    prospect = relationship("Prospect", back_populates="activities")
    user = relationship("User")

class ImportBatch(Base):
    __tablename__ = "import_batches"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String, unique=True, nullable=False, index=True)  # UUID
    file_name = Column(String, nullable=False)
    file_size = Column(Integer, nullable=True)

    # Import Stats
    total_records = Column(Integer, nullable=False)
    successful_imports = Column(Integer, default=0)
    failed_imports = Column(Integer, default=0)
    errors = Column(JSON, nullable=True)  # List of errors with row numbers

    # Metadata
    imported_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    mapping_used = Column(JSON, nullable=True)  # Column mappings used

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    imported_by = relationship("User")

# ============================================================================
# FINANCIAL PLANNING SYSTEM
# ============================================================================

class ProductType(str, enum.Enum):
    EQUITY = "EQUITY"  # Individual stocks
    MUTUAL_FUND = "MUTUAL_FUND"
    ETF = "ETF"
    BOND = "BOND"
    INSURANCE = "INSURANCE"
    # PMS = "PMS"  # Temporarily disabled - will be added later
    # AIF = "AIF"  # Temporarily disabled - will be added later

class GoalType(str, enum.Enum):
    RETIREMENT = "RETIREMENT"
    EDUCATION = "EDUCATION"
    HOUSE = "HOUSE"
    CAR = "CAR"
    VACATION = "VACATION"
    WEALTH_CREATION = "WEALTH_CREATION"
    MARRIAGE = "MARRIAGE"
    EMERGENCY_FUND = "EMERGENCY_FUND"
    OTHER = "OTHER"

class PlanStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"

class InvestmentType(str, enum.Enum):
    LUMPSUM = "LUMPSUM"
    SIP = "SIP"
    BOTH = "BOTH"

# Product Catalog
class FinancialProduct(Base):
    __tablename__ = "financial_products"

    id = Column(Integer, primary_key=True, index=True)

    # Basic Info
    product_type = Column(Enum(ProductType), nullable=False, index=True)
    product_code = Column(String, unique=True, nullable=False, index=True)  # ISIN/NSE Symbol
    product_name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)

    # For Stocks
    exchange = Column(String, nullable=True)  # NSE/BSE
    sector = Column(String, nullable=True, index=True)
    market_cap_category = Column(String, nullable=True)  # Large/Mid/Small
    price = Column(Float, nullable=True)
    pe_ratio = Column(Float, nullable=True)
    pb_ratio = Column(Float, nullable=True)
    dividend_yield = Column(Float, nullable=True)
    market_cap = Column(Float, nullable=True)  # in crores

    # For Mutual Funds
    fund_house = Column(String, nullable=True, index=True)
    category = Column(String, nullable=True, index=True)  # Equity, Debt, Hybrid
    sub_category = Column(String, nullable=True)  # Large Cap, Mid Cap, etc.
    nav = Column(Float, nullable=True)
    aum = Column(Float, nullable=True)  # in crores
    fund_manager = Column(String, nullable=True)
    expense_ratio = Column(Float, nullable=True)
    exit_load = Column(Float, nullable=True)
    min_investment = Column(Float, nullable=True)
    min_sip = Column(Float, nullable=True)

    # Performance Metrics
    return_1m = Column(Float, nullable=True)
    return_3m = Column(Float, nullable=True)
    return_6m = Column(Float, nullable=True)
    return_1y = Column(Float, nullable=True)
    return_3y = Column(Float, nullable=True)
    return_5y = Column(Float, nullable=True)
    return_since_inception = Column(Float, nullable=True)

    # Risk Metrics
    standard_deviation = Column(Float, nullable=True)
    beta = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    sortino_ratio = Column(Float, nullable=True)

    # Benchmark
    benchmark = Column(String, nullable=True)

    # Commission
    commission_rate = Column(Float, nullable=True)  # For revenue tracking

    # Status
    is_active = Column(Boolean, default=True)
    is_recommended = Column(Boolean, default=False)  # Featured products

    # Timestamps
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Financial Plan
class FinancialPlan(Base):
    __tablename__ = "financial_plans"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)

    plan_name = Column(String, nullable=False)
    plan_date = Column(Date, nullable=False)
    status = Column(Enum(PlanStatus), default=PlanStatus.DRAFT, index=True)

    # Client Profile
    age = Column(Integer, nullable=False)
    annual_income = Column(Float, nullable=False)
    monthly_expenses = Column(Float, nullable=True)
    existing_assets = Column(Float, default=0)
    existing_liabilities = Column(Float, default=0)
    number_of_dependents = Column(Integer, default=0)
    occupation = Column(String, nullable=True)

    # Risk Profile
    risk_score = Column(Integer, nullable=True)  # 0-100
    risk_category = Column(Enum(RiskCategory), nullable=True)
    investment_horizon = Column(Integer, nullable=True)  # in years
    risk_capacity = Column(String, nullable=True)  # High/Medium/Low
    risk_tolerance = Column(String, nullable=True)

    # Recommended Asset Allocation (%)
    recommended_equity = Column(Float, nullable=True)
    recommended_debt = Column(Float, nullable=True)
    recommended_gold = Column(Float, nullable=True)
    recommended_liquid = Column(Float, nullable=True)
    recommended_alternative = Column(Float, nullable=True)

    # Actual Allocation (%)
    actual_equity = Column(Float, default=0)
    actual_debt = Column(Float, default=0)
    actual_gold = Column(Float, default=0)
    actual_liquid = Column(Float, default=0)
    actual_alternative = Column(Float, default=0)

    # Total Investment
    total_investment = Column(Float, default=0)
    monthly_sip = Column(Float, default=0)
    lumpsum_amount = Column(Float, default=0)

    # Notes
    advisor_notes = Column(Text, nullable=True)
    client_preferences = Column(JSON, nullable=True)

    # Timestamps
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    presented_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    customer = relationship("Customer", back_populates="financial_plans")
    created_by = relationship("User")
    goals = relationship("FinancialGoal", back_populates="plan", cascade="all, delete-orphan")
    portfolio_components = relationship("PortfolioComponent", back_populates="plan", cascade="all, delete-orphan")

# Add relationship to Customer model
Customer.financial_plans = relationship("FinancialPlan", back_populates="customer")

# Financial Goals
class FinancialGoal(Base):
    __tablename__ = "financial_goals"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("financial_plans.id"), nullable=False)

    goal_name = Column(String, nullable=False)
    goal_type = Column(Enum(GoalType), nullable=False)
    target_amount = Column(Float, nullable=False)
    current_corpus = Column(Float, default=0)
    years_to_goal = Column(Integer, nullable=False)
    priority = Column(Integer, default=2)  # 1=High, 2=Medium, 3=Low

    # Assumptions
    expected_return = Column(Float, default=12.0)  # %
    inflation_rate = Column(Float, default=6.0)  # %

    # Calculated Values
    inflation_adjusted_target = Column(Float, nullable=True)
    required_monthly_sip = Column(Float, nullable=True)
    required_lumpsum = Column(Float, nullable=True)
    shortfall = Column(Float, nullable=True)

    # Status
    is_achieved = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    plan = relationship("FinancialPlan", back_populates="goals")

# Portfolio Components
class PortfolioComponent(Base):
    __tablename__ = "portfolio_components"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("financial_plans.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("financial_products.id"), nullable=False)

    # Allocation
    allocation_percentage = Column(Float, nullable=False)
    investment_amount = Column(Float, nullable=False)
    investment_type = Column(Enum(InvestmentType), default=InvestmentType.BOTH)

    # SIP Details
    sip_amount = Column(Float, default=0)
    sip_frequency = Column(String, default="MONTHLY")  # MONTHLY/QUARTERLY
    sip_duration_months = Column(Integer, default=12)

    # Lumpsum Details
    lumpsum_amount = Column(Float, default=0)

    # Projections
    expected_return = Column(Float, nullable=True)
    projected_value_1y = Column(Float, nullable=True)
    projected_value_3y = Column(Float, nullable=True)
    projected_value_5y = Column(Float, nullable=True)

    # Goal Mapping
    goal_id = Column(Integer, ForeignKey("financial_goals.id"), nullable=True)

    # Notes
    rationale = Column(Text, nullable=True)
    risk_contribution = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    plan = relationship("FinancialPlan", back_populates="portfolio_components")
    product = relationship("FinancialProduct")
    goal = relationship("FinancialGoal")

# Risk Profiling
class RiskProfile(Base):
    __tablename__ = "risk_profiles"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("financial_plans.id"), nullable=True)

    # Questionnaire Responses (JSON format)
    responses = Column(JSON, nullable=False)

    # Calculated Scores
    total_score = Column(Integer, nullable=False)
    risk_category = Column(Enum(RiskCategory), nullable=False)
    risk_tolerance_score = Column(Integer, nullable=True)
    risk_capacity_score = Column(Integer, nullable=True)

    # Recommendations
    recommended_equity_range = Column(String, nullable=True)  # "50-70%"
    investment_personality = Column(String, nullable=True)

    completed_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    customer = relationship("Customer")

# Benchmarks
class Benchmark(Base):
    __tablename__ = "benchmarks"

    id = Column(Integer, primary_key=True, index=True)

    benchmark_name = Column(String, nullable=False, unique=True)
    benchmark_code = Column(String, nullable=False, unique=True)  # ^NSEI, ^BSESN
    category = Column(String, nullable=True)  # Broad Market, Sector, etc.
    description = Column(Text, nullable=True)

    # Current Data
    current_value = Column(Float, nullable=True)

    # Historical Returns
    return_1m = Column(Float, nullable=True)
    return_3m = Column(Float, nullable=True)
    return_6m = Column(Float, nullable=True)
    return_1y = Column(Float, nullable=True)
    return_3y = Column(Float, nullable=True)
    return_5y = Column(Float, nullable=True)

    # Volatility
    standard_deviation = Column(Float, nullable=True)

    last_updated = Column(DateTime(timezone=True), server_default=func.now())

# Model Portfolios (Pre-built baskets)
class ModelPortfolio(Base):
    __tablename__ = "model_portfolios"

    id = Column(Integer, primary_key=True, index=True)

    portfolio_name = Column(String, nullable=False)
    portfolio_type = Column(String, nullable=False)  # Thematic, Smart Beta, Conservative, etc.
    description = Column(Text, nullable=True)

    # Target Profile
    risk_category = Column(Enum(RiskCategory), nullable=True)
    min_investment = Column(Float, nullable=True)

    # Performance (if backtested)
    expected_return = Column(Float, nullable=True)
    historical_return_1y = Column(Float, nullable=True)
    historical_return_3y = Column(Float, nullable=True)

    # Components (JSON: [{product_id, allocation_percentage}])
    components = Column(JSON, nullable=False)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Client Profiling Questionnaire Invites
class QuestionnaireInviteStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"

class QuestionnaireInvite(Base):
    __tablename__ = "questionnaire_invites"

    id = Column(Integer, primary_key=True, index=True)

    # Invite Details
    invite_token = Column(String, unique=True, nullable=False, index=True)  # Unique shareable token
    recipient_name = Column(String, nullable=False)
    recipient_email = Column(String, nullable=False, index=True)
    recipient_phone = Column(String, nullable=True)

    # Status
    status = Column(Enum(QuestionnaireInviteStatus), default=QuestionnaireInviteStatus.PENDING, index=True)

    # Tracking
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Optional expiry
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Auto-create prospect on completion
    auto_create_prospect = Column(Boolean, default=True)
    created_prospect_id = Column(Integer, ForeignKey("prospects.id"), nullable=True)

    # Response data (will be populated when submitted)
    response_data = Column(JSON, nullable=True)  # Complete questionnaire response

    # Metadata
    notes = Column(Text, nullable=True)  # Internal notes about this invite
    custom_message = Column(Text, nullable=True)  # Personalized message in invite email

    # Relationships
    created_by = relationship("User", foreign_keys=[created_by_id])
    created_prospect = relationship("Prospect", foreign_keys=[created_prospect_id])

# Client Profiling Responses (detailed storage)
class ClientProfilingResponse(Base):
    __tablename__ = "client_profiling_responses"

    id = Column(Integer, primary_key=True, index=True)

    invite_id = Column(Integer, ForeignKey("questionnaire_invites.id"), nullable=False)
    prospect_id = Column(Integer, ForeignKey("prospects.id"), nullable=True)

    # Personal Information
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    date_of_birth = Column(Date, nullable=True)
    occupation = Column(String, nullable=True)
    annual_income = Column(Float, nullable=True)

    # Financial Information
    monthly_income = Column(Float, nullable=True)
    monthly_expenses = Column(Float, nullable=True)
    existing_investments = Column(Float, nullable=True)
    existing_liabilities = Column(Float, nullable=True)
    emergency_fund_months = Column(Integer, nullable=True)

    # Investment Preferences
    investment_experience = Column(String, nullable=True)  # Beginner, Intermediate, Advanced
    preferred_investment_types = Column(JSON, nullable=True)  # ["Equity", "Mutual Funds", etc.]
    investment_timeline = Column(String, nullable=True)  # Short-term, Medium-term, Long-term
    monthly_investment_capacity = Column(Float, nullable=True)
    lumpsum_availability = Column(Float, nullable=True)

    # Goals (JSON array of goals)
    financial_goals = Column(JSON, nullable=True)
    # Example: [
    #   {"type": "RETIREMENT", "amount": 50000000, "years": 20, "priority": "HIGH"},
    #   {"type": "EDUCATION", "amount": 2000000, "years": 10, "priority": "HIGH"}
    # ]

    # Risk Assessment
    risk_questionnaire_responses = Column(JSON, nullable=True)  # Risk questionnaire answers
    calculated_risk_score = Column(Integer, nullable=True)
    calculated_risk_category = Column(Enum(RiskCategory), nullable=True)

    # Additional Information
    current_advisor = Column(String, nullable=True)  # Do they have an existing advisor
    how_did_you_hear = Column(String, nullable=True)  # Referral source
    specific_requirements = Column(Text, nullable=True)  # Open text for specific needs
    preferred_contact_time = Column(String, nullable=True)

    # Timestamps
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    invite = relationship("QuestionnaireInvite")
    prospect = relationship("Prospect")
