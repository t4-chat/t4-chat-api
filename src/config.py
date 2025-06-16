from functools import lru_cache
from typing import Dict, List

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from src.logging.logging_config import get_logger

load_dotenv()  # need this to load model keys

logger = get_logger(__name__)

class ModelHostSettings(BaseModel):
    api_key: str


class Settings(BaseSettings):
    PROJECT_NAME: str = Field("AGG-AI", env="PROJECT_NAME")
    PROJECT_DESCRIPTION: str = Field("API for aggregating multiple AI providers", env="PROJECT_DESCRIPTION")
    VERSION: str = Field("1.0.0", env="VERSION")

    ENVIRONMENT: str = Field("development", env="ENVIRONMENT")
    GOOGLE_CLIENT_ID: str = Field(..., env="GOOGLE_CLIENT_ID")
    JWT_SECRET_KEY: str = Field(..., env="JWT_SECRET_KEY")
    JWT_EXPIRATION_MINUTES: int = Field(60 * 24 * 60, env="JWT_EXPIRATION_MINUTES")

    TITLE_GENERATION_MODEL: str = Field("openai/gpt-4.1-nano", env="TITLE_GENERATION_MODEL")

    DATABASE_URL: str = Field("postgresql://postgres:postgres@localhost:5433/agg-ai", env="DATABASE_URL")
    DB_POOL_SIZE: int = Field(30, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(100, env="DB_MAX_OVERFLOW")
    DB_POOL_RECYCLE: int = Field(3600, env="DB_POOL_RECYCLE")

    # OpenTelemetry settings
    OTEL_SERVICE_NAME: str = Field("agg-ai-api", env="OTEL_SERVICE_NAME")
    OTEL_EXPORTER_OTLP_ENDPOINT: str = Field("jaeger:4317", env="OTEL_EXPORTER_OTLP_ENDPOINT")

    GCP_BUCKET_NAME: str = Field("agg-ai-bucket", env="GCP_BUCKET_NAME")
    GCP_PROJECT_ID: str = Field("dev-agg-ai", env="GCP_PROJECT_ID")

    MODEL_HOSTS: Dict[str, ModelHostSettings] = Field(default_factory=dict)

    MOCK_AI_RESPONSE: bool = Field(False, env="MOCK_AI_RESPONSE")

    ADMIN_EMAILS: List[str] = Field(
        ["avdieiev.oleksii@gmail.com", "stepun.tita@gmail.com", "pxlxpenko@gmail.com", "ostashko4@gmail.com"],
        env="ADMIN_EMAILS"
    )

    # Model api keys
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: str = Field(..., env="ANTHROPIC_API_KEY") 
    DEEPSEEK_API_KEY: str = Field(..., env="DEEPSEEK_API_KEY")
    GEMINI_API_KEY: str = Field(..., env="GEMINI_API_KEY")
    XAI_API_KEY: str = Field(..., env="XAI_API_KEY")
    GROQ_API_KEY: str = Field(..., env="GROQ_API_KEY")
    TOGETHERAI_API_KEY: str = Field(..., env="TOGETHERAI_API_KEY")
    LLAMA_API_KEY: str = Field(..., env="LLAMA_API_KEY")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._load_model_providers()

    def _load_model_providers(self):
        def mask_api_key(key: str) -> str:
            return f"{key[:3]}......{key[-3:]}" if key else "null"

        logger.info(f"OpenAI API Key: {mask_api_key(self.OPENAI_API_KEY)}")
        logger.info(f"Anthropic API Key: {mask_api_key(self.ANTHROPIC_API_KEY)}")
        logger.info(f"DeepSeek API Key: {mask_api_key(self.DEEPSEEK_API_KEY)}")
        logger.info(f"Gemini API Key: {mask_api_key(self.GEMINI_API_KEY)}")
        logger.info(f"XAI API Key: {mask_api_key(self.XAI_API_KEY)}")
        logger.info(f"Groq API Key: {mask_api_key(self.GROQ_API_KEY)}")
        logger.info(f"Together AI API Key: {mask_api_key(self.TOGETHERAI_API_KEY)}")
        logger.info(f"Llama API Key: {mask_api_key(self.LLAMA_API_KEY)}")

        # OpenAI
        self.MODEL_HOSTS["openai"] = ModelHostSettings(api_key=self.OPENAI_API_KEY)

        # Anthropic
        self.MODEL_HOSTS["anthropic"] = ModelHostSettings(api_key=self.ANTHROPIC_API_KEY)

        # DeepSeek
        self.MODEL_HOSTS["deepseek"] = ModelHostSettings(api_key=self.DEEPSEEK_API_KEY)

        # Gemini
        self.MODEL_HOSTS["gemini"] = ModelHostSettings(api_key=self.GEMINI_API_KEY)

        # XAI
        self.MODEL_HOSTS["xai"] = ModelHostSettings(api_key=self.XAI_API_KEY)

        # Groq
        self.MODEL_HOSTS["groq"] = ModelHostSettings(api_key=self.GROQ_API_KEY)

        # Together AI
        self.MODEL_HOSTS["together_ai"] = ModelHostSettings(api_key=self.TOGETHERAI_API_KEY)
        
        # Llama
        self.MODEL_HOSTS["meta_llama"] = ModelHostSettings(api_key=self.LLAMA_API_KEY)

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Allow extra keys in settings without validation errors


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
