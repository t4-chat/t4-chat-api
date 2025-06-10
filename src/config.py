from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    PROJECT_NAME: str = "Agg AI API"
    PROJECT_DESCRIPTION: str = "API for aggregating multiple AI providers"
    VERSION: str = "1.0.0"
    
    ENVIRONMENT: str = "development"
    GOOGLE_CLIENT_ID: str
    JWT_SECRET_KEY: str
    JWT_EXPIRATION_MINUTES: int = 60 * 24 * 60  # 30 days

    TITLE_GENERATION_MODEL: str = "openai/gpt-4o"
    
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5433/agg-ai"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Allow extra keys in settings without validation errors

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()