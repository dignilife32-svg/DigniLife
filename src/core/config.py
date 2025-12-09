"""
DigniLife Platform - Configuration
"""
from pydantic_settings import BaseSettings
from typing import List, Union


class Settings(BaseSettings):
    """Application settings"""
    
    # App
    APP_NAME: str = "DigniLife"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str
    
    # Security
    SECRET_KEY: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRATION_DAYS: int = 30
    
    # CORS - Accept both string and list
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:3000,http://localhost:8000"
    
    # Face Liveness API (placeholder for now)
    LIVENESS_API_URL: str = ""
    LIVENESS_API_KEY: str = ""
    
    # Currency Exchange API
    FX_API_URL: str = "https://api.exchangerate-api.com/v4/latest/USD"
    FX_UPDATE_INTERVAL_HOURS: int = 1
    
    # AI Services (placeholder for now)
    AI_VALIDATION_API: str = ""
    AI_CHAT_API: str = ""
    
    # Email (placeholder for now)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS_ORIGINS to list"""
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        return self.CORS_ORIGINS
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()