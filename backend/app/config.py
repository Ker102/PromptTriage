"""
Application configuration loaded from environment variables.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    # Google AI
    google_api_key: str = ""
    
    # Redis Cloud
    redis_url: str = ""  # redis://default:password@host:port
    redis_index_name: str = "prompttriage_prompts"
    
    # LangCache (Redis Cloud)
    langcache_url: str = ""  # https://xxx.langcache.redis.io
    langcache_api_key: str = ""
    
    # Frontend
    frontend_url: str = "http://localhost:3000"
    
    # Embedding model
    embedding_model: str = "all-MiniLM-L6-v2"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()


settings = get_settings()
