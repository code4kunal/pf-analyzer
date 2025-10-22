from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import settings
import models
import schemas
import secrets
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from database import get_db

# ============================================================================
# PASSWORD HASHING
# ============================================================================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password for storing"""
    return pwd_context.hash(password)

def generate_temp_password(length: int = 12) -> str:
    """Generate a secure temporary password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    # Ensure password has at least one of each required character type
    password = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%^&*")
    ]
    # Fill the rest randomly
    password += [secrets.choice(alphabet) for _ in range(length - 4)]
    # Shuffle to avoid predictable patterns
    secrets.SystemRandom().shuffle(password)
    return ''.join(password)

# ============================================================================
# JWT TOKEN HANDLING
# ============================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def verify_token(token: str) -> Optional[schemas.TokenData]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: int = payload.get("user_id")
        email: str = payload.get("sub")
        role: str = payload.get("role")

        if email is None or user_id is None:
            return None

        return schemas.TokenData(
            user_id=user_id,
            email=email,
            role=models.UserRole(role) if role else None
        )
    except JWTError:
        return None

# ============================================================================
# AUTHENTICATION
# ============================================================================

def authenticate_user(db: Session, email: str, password: str) -> Optional[models.User]:
    """Authenticate a user by email and password"""
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        return None
    if not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

# ============================================================================
# DEPENDENCIES
# ============================================================================

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> models.User:
    """Get the current authenticated user from JWT token"""
    token = credentials.credentials

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = verify_token(token)
    if token_data is None or token_data.email is None:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.email == token_data.email).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    return user

def get_current_active_user(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    """Get current active user (wrapper for clarity)"""
    return current_user

# ============================================================================
# RBAC (Role-Based Access Control)
# ============================================================================

def require_role(*allowed_roles: models.UserRole):
    """Dependency to check if user has required role"""
    def role_checker(current_user: models.User = Depends(get_current_user)) -> models.User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {', '.join([r.value for r in allowed_roles])}"
            )
        return current_user
    return role_checker

def require_admin(current_user: models.User = Depends(get_current_user)) -> models.User:
    """Dependency to require admin role"""
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

def check_resource_access(
    current_user: models.User,
    resource_user_id: Optional[int] = None
) -> bool:
    """Check if user can access a resource (admins can access all, employees only their own)"""
    if current_user.role == models.UserRole.ADMIN:
        return True
    if resource_user_id is None:
        return True
    return current_user.id == resource_user_id

# ============================================================================
# EMAIL SERVICE
# ============================================================================

def send_email(
    to_email: str,
    subject: str,
    body_html: str,
    body_text: Optional[str] = None
) -> bool:
    """Send an email using configured SMTP settings"""
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
        msg['To'] = to_email
        msg['Subject'] = subject

        # Add text and HTML parts
        if body_text:
            part1 = MIMEText(body_text, 'plain')
            msg.attach(part1)

        part2 = MIMEText(body_html, 'html')
        msg.attach(part2)

        # Send email
        if not settings.smtp_password:
            print(f"⚠️  SMTP not configured. Email would be sent to {to_email}")
            print(f"Subject: {subject}")
            return True

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(msg)

        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def send_invitation_email(user: models.User, temp_password: str) -> bool:
    """Send invitation email with temporary password to new user"""
    subject = f"Welcome to {settings.app_name} - Your Account Details"

    body_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background-color: #f9f9f9; }}
            .credentials {{ background-color: #fff; padding: 15px; border-left: 4px solid #4CAF50; margin: 20px 0; }}
            .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #777; }}
            .button {{ display: inline-block; padding: 10px 20px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Welcome to {settings.app_name}</h1>
            </div>
            <div class="content">
                <p>Hi {user.full_name},</p>
                <p>You have been invited to join {settings.app_name} as a <strong>{user.role.value}</strong>.</p>

                <div class="credentials">
                    <h3>Your Login Credentials:</h3>
                    <p><strong>Email:</strong> {user.email}</p>
                    <p><strong>Temporary Password:</strong> {temp_password}</p>
                    <p><strong>Login URL:</strong> {settings.frontend_url}/login</p>
                </div>

                <p><strong>⚠️ Important:</strong> This is a temporary password. You will be required to change it upon your first login.</p>

                <p style="text-align: center; margin-top: 30px;">
                    <a href="{settings.frontend_url}/login" class="button">Login Now</a>
                </p>
            </div>
            <div class="footer">
                <p>If you have any questions, please contact your administrator.</p>
                <p>&copy; 2024 {settings.app_name}. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

    body_text = f"""
    Welcome to {settings.app_name}

    Hi {user.full_name},

    You have been invited to join {settings.app_name} as a {user.role.value}.

    Your Login Credentials:
    Email: {user.email}
    Temporary Password: {temp_password}
    Login URL: {settings.frontend_url}/login

    ⚠️ Important: This is a temporary password. You will be required to change it upon your first login.

    If you have any questions, please contact your administrator.

    © 2024 {settings.app_name}. All rights reserved.
    """

    return send_email(user.email, subject, body_html, body_text)

def send_password_reset_email(user: models.User, temp_password: str) -> bool:
    """Send password reset email to user"""
    subject = f"{settings.app_name} - Password Reset"

    body_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #2196F3; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background-color: #f9f9f9; }}
            .credentials {{ background-color: #fff; padding: 15px; border-left: 4px solid #2196F3; margin: 20px 0; }}
            .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #777; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Password Reset</h1>
            </div>
            <div class="content">
                <p>Hi {user.full_name},</p>
                <p>Your password has been reset by an administrator.</p>

                <div class="credentials">
                    <h3>Your New Temporary Password:</h3>
                    <p><strong>Password:</strong> {temp_password}</p>
                    <p><strong>Login URL:</strong> {settings.frontend_url}/login</p>
                </div>

                <p><strong>⚠️ Important:</strong> Please change this password immediately after logging in.</p>
            </div>
            <div class="footer">
                <p>If you did not request this change, please contact your administrator immediately.</p>
                <p>&copy; 2024 {settings.app_name}. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

    body_text = f"""
    Password Reset - {settings.app_name}

    Hi {user.full_name},

    Your password has been reset by an administrator.

    Your New Temporary Password: {temp_password}
    Login URL: {settings.frontend_url}/login

    ⚠️ Important: Please change this password immediately after logging in.

    If you did not request this change, please contact your administrator immediately.

    © 2024 {settings.app_name}. All rights reserved.
    """

    return send_email(user.email, subject, body_html, body_text)

# ============================================================================
# ACTIVITY LOGGING
# ============================================================================

def log_activity(
    db: Session,
    entity_type: str,
    entity_id: int,
    action: str,
    description: str,
    user_id: Optional[int] = None,
    changes: Optional[dict] = None
):
    """Log an activity to the activity log"""
    activity_log = models.ActivityLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        description=description,
        user_id=user_id,
        changes=changes
    )
    db.add(activity_log)
    db.commit()
