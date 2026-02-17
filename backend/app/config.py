"""Application configuration using environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    # API Configuration
    api_title: str = "Auto Structure Analysis API"
    api_version: str = "0.1.0"
    api_description: str = "Automated structural analysis using computer vision and FEA"
    
    # CORS Configuration
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "https://johntfoster.github.io"
    ]
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 30
    
    # File Upload Limits
    max_upload_size_mb: int = 10
    allowed_file_types: list[str] = ["image/jpeg", "image/png"]
    
    # Authentication
    api_key_enabled: bool = False
    api_key: str | None = None
    
    # Database
    database_url: str = "sqlite:///./analyses.db"
    
    # Google Cloud
    gcp_project_id: str | None = None
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


# Global settings instance
settings = Settings()
