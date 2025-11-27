from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    # Project
    PROJECT_NAME: str = "Capvero Backend API"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "https://app.capvero.io",
        "https://app-dev.capvero.io",
        "https://app-stage.capvero.io",
    ]
    
    # Cloud Storage
    GCS_BUCKET_NAME: str = "capvero-exports"
    
    # External APIs
    BEXIO_CLIENT_ID: str = ""
    BEXIO_CLIENT_SECRET: str = ""
    BEXIO_REDIRECT_URI: str = ""
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
