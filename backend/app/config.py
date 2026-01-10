"""
Application configuration loaded from environment variables.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    # Google AI
    google_api_key: str = ""
    
    # Redis Cloud (Hot Cache)
    redis_url: str = ""
    redis_index_name: str = "prompttriage_hot"
    
    # Pinecone (Full Corpus)
    pinecone_api_key: str = ""
    pinecone_index_name: str = "prompttriage-prompts"
    pinecone_environment: str = "us-east-1"
    
    # LangCache (Redis Cloud)
    langcache_url: str = ""
    langcache_api_key: str = ""
    
    # Frontend
    frontend_url: str = "http://localhost:3000"
    
    # Embedding model (768d for better quality)
    embedding_model: str = "all-mpnet-base-v2"
    
    # Cache settings
    cache_top_k: int = 10  # How many results to cache in Redis after Pinecone query
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()


settings = get_settings()
