from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database - Railway provides DATABASE_URL automatically for PostgreSQL
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./portfolio.db")

    # Security
    secret_key: str = "your-secret-key-change-this"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 43200

    # Zerodha Kite API
    kite_api_key: Optional[str] = None
    kite_api_secret: Optional[str] = None
    kite_request_token: Optional[str] = None
    kite_access_token: Optional[str] = None

    # App Settings
    app_name: str = "Portfolio Analyzer"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000

    class Config:
        env_file = ".env"

settings = Settings()