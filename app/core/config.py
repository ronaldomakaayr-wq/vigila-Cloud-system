import os
from typing import Optional
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    PROJECT_NAME: str = "VIGILA - Cloud Video Surveillance"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "vigila_secret_key_cloud_production_2026_super_secure")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    ALGORITHM: str = "HS256"
    
    # Database (RDS PostgreSQL / Local SQLite fallback)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./vigila_cloud.db"
    )
    
    # AWS Configuration
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID", None)
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY", None)
    AWS_SESSION_TOKEN: Optional[str] = os.getenv("AWS_SESSION_TOKEN", None)
    
    # S3 Settings
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "vigila-surveillance-recordings-archive-prod")
    S3_PRESIGNED_URL_EXPIRATION: int = 900  # 15 minutes
    
    # Systems Manager (SSM)
    SSM_PARAMETER_PREFIX: str = "/vigila/production/"
    
    # Mock / Emulation Mode for local execution without AWS account
    AWS_MOCK_MODE: bool = os.getenv("AWS_MOCK_MODE", "true").lower() in ("true", "1", "yes")

settings = Settings()

