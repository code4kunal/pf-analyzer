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

class RiskProfile(str, enum.Enum):
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
    risk_profile = Column(Enum(RiskProfile), nullable=True)
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
