"""
Application configuration loaded from environment variables.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    # Google AI
    google_api_key: str = ""
    
    # Vector DB
    chroma_persist_dir: str = "./chroma_data"
    
    # Frontend
    frontend_url: str = "http://localhost:3000"
    
    # Optional: Redis caching
    upstash_redis_url: str = ""
    upstash_redis_token: str = ""
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()


settings = get_settings()
