"""
Application configuration loaded from environment variables.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    # Google AI (Gemini for embeddings + generation)
    google_api_key: str = ""
    
    # Pinecone (Full Corpus)
    pinecone_api_key: str = ""
    pinecone_index_name: str = "prompttriage-prompts"
    pinecone_environment: str = "us-east-1"
    
    # Frontend
    frontend_url: str = "http://localhost:3000"
    
    # Embedding settings
    # Using Gemini embeddings (768d) for better quality
    embedding_model: str = "gemini-embedding-001"
    embedding_dimensions: int = 768
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()


settings = get_settings()
