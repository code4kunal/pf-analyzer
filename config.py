from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """
    Application settings for local development and production (Railway).

    - Environment variables take priority (Railway production)
    - Falls back to .env file (local development)
    - Railway automatically provides DATABASE_URL for PostgreSQL
    """

    # Environment detection (optional - for conditional logic)
    environment: str = os.getenv("ENVIRONMENT", "development")

    # Database - Railway provides DATABASE_URL automatically
    database_url: str = os.getenv("DATABASE_URL", "postgresql://localhost/growfolio")

    # Security
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 43200  # 30 days

    # Google API (for Google Meet & Gmail SMTP)
    google_client_id: Optional[str] = os.getenv("GOOGLE_CLIENT_ID")
    google_client_secret: Optional[str] = os.getenv("GOOGLE_CLIENT_SECRET")
    google_redirect_uri: Optional[str] = os.getenv("GOOGLE_REDIRECT_URI")

    # Email Configuration (Google SMTP)
    smtp_host: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "help@grow-folio.in")
    smtp_password: Optional[str] = os.getenv("SMTP_PASSWORD")
    smtp_from_email: str = os.getenv("SMTP_FROM_EMAIL", "help@grow-folio.in")
    smtp_from_name: str = os.getenv("SMTP_FROM_NAME", "GrowFolio")

    # Storage
    storage_type: str = os.getenv("STORAGE_TYPE", "local")  # local or s3
    upload_dir: str = os.getenv("UPLOAD_DIR", "./uploads")

    # AWS S3 (for future use)
    aws_access_key_id: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_s3_bucket: Optional[str] = os.getenv("AWS_S3_BUCKET")
    aws_region: str = os.getenv("AWS_REGION", "ap-south-1")

    # App Settings
    app_name: str = "GrowFolio CMS"
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"
    host: str = "0.0.0.0"
    port: int = int(os.getenv("PORT", "8000"))

    # Frontend URL (for email links)
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:8000")

    class Config:
        env_file = ".env"  # Used for local development only
        env_file_encoding = "utf-8"
        extra = "ignore"  # Don't fail if .env doesn't exist

    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment.lower() == "production" or not self.debug

settings = Settings()