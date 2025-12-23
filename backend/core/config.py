"""
Application configuration and settings.
Uses environment variables with sensible defaults.
"""

import os
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()


def parse_cors_origins(origins_str: Optional[str]) -> List[str]:
    """Parse comma-separated CORS origins from environment variable."""
    if not origins_str:
        return []
    return [origin.strip() for origin in origins_str.split(",") if origin.strip()]


class Settings:
    """Application settings loaded from environment."""
    
    # API Keys
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    BRIGHT_DATA_API_TOKEN: str = os.getenv("BRIGHT_DATA_API_TOKEN", "")
    
    # MCP Configuration
    MCP_MODE: str = os.getenv("MCP_MODE", "stdio").lower()  # "sse", "stdio", or "mock"
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8097"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # CORS Configuration - Configurable via environment
    # Set CORS_ORIGINS="https://yourdomain.com,https://app.yourdomain.com" in production
    _default_origins = [
        # Development
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:3014",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3014",
        # Production
        "https://multiplatform.apexneural.cloud",
        "https://multiplatform-api.apexneural.cloud",
    ]
    _env_origins = parse_cors_origins(os.getenv("CORS_ORIGINS"))
    CORS_ORIGINS: List[str] = _env_origins if _env_origins else _default_origins
    
    # LLM Configuration
    LLM_BASE_URL: str = "https://openrouter.ai/api/v1"
    
    SEARCH_MODEL: str = os.getenv("SEARCH_MODEL", "openrouter/openai/gpt-4o")
    SEARCH_TEMPERATURE: float = 0.0
    
    SPECIALIST_MODEL: str = os.getenv("SPECIALIST_MODEL", "openrouter/openai/o3-mini")
    SPECIALIST_TEMPERATURE: float = 0.1
    
    RESPONSE_MODEL: str = os.getenv("RESPONSE_MODEL", "openrouter/google/gemini-2.0-flash-001")
    RESPONSE_TEMPERATURE: float = 0.3


# Global settings instance
settings = Settings()

