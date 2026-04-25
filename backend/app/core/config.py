from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "CareerOpsV2"
    DEBUG: bool = False
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Email
    SMTP_HOST: str
    SMTP_PORT: int = 587
    SMTP_USER: str
    SMTP_PASSWORD: str
    EMAIL_FROM: str

    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"

    # Oxylabs
    OXYLABS_USERNAME: str
    OXYLABS_PASSWORD: str
    OXYLABS_USER_ID: str = ""
    OXYLABS_TOKEN: str = ""

    # Token costs
    TOKEN_COST_RESIDENTIAL_IP: int = 20
    TOKEN_COST_SEARCH_4H: int = 0
    TOKEN_COST_SEARCH_2H: int = 100
    TOKEN_COST_AI_EVALUATION: int = 50

    class Config:
        env_file = ".env"


settings = Settings()
