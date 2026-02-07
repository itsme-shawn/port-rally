"""Configuration settings for AI Advisor service."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # AI Service
    google_api_key: str
    gemini_model: str = "gemini-1.5-flash-latest"

    # Database
    database_url: str

    # Redis
    redis_url: str
    redis_queue_name: str = "queue:portfolio_analysis"
    redis_job_prefix: str = "job:"

    # Service
    port: int = 8081
    log_level: str = "INFO"

    # Rate Limiting
    max_analyses_per_user_per_month: int = 10
    cache_ttl_hours: int = 24

    # Prompt Settings
    max_input_tokens: int = 10000
    max_output_tokens: int = 2000
    temperature: float = 0.3  # Lower for more consistent analysis


settings = Settings()
