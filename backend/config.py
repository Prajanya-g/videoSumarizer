"""
Configuration settings for the video summarizer application.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application settings and configuration."""
    
    # API Configuration
    API_TITLE = "Video Summarizer API"
    API_DESCRIPTION = """
    A comprehensive video summarization service that processes videos to create highlights and transcripts.
    
    ## Features
    
    * **User Authentication**: JWT-based authentication with user registration and login
    * **Video Processing**: Upload videos and generate summaries with highlights
    * **Job Management**: Track processing status and manage video jobs
    * **File Management**: Serve processed videos, thumbnails, and transcripts
    
    ## Authentication
    
    Most endpoints require authentication. Include the JWT token in the Authorization header:
    ```
    Authorization: Bearer <your-jwt-token>
    ```
    
    ## Rate Limiting
    
    API calls are rate-limited to prevent abuse. Please implement appropriate retry logic.
    
    ## Error Handling
    
    The API uses standard HTTP status codes and returns detailed error messages in JSON format.
    """
    API_VERSION = "1.0.0"
    API_CONTACT_NAME = "Video Summarizer Support"
    API_CONTACT_EMAIL = "support@videosummarizer.com"
    API_LICENSE_NAME = "MIT"
    API_LICENSE_URL = "https://opensource.org/licenses/MIT"
    
    # Server Configuration
    HOST = "0.0.0.0"
    PORT = 8000
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # Database Configuration
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./video_summarizer.db")
    
    # JWT Configuration
    JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
    
    # CORS Configuration
    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8080"
    ]
    
    # File Storage Configuration
    UPLOAD_DIR = Path("data/jobs")
    MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
    ALLOWED_VIDEO_TYPES = [
        "video/mp4",
        "video/avi",
        "video/mov",
        "video/wmv",
        "video/flv",
        "video/webm"
    ]
    
    # Processing Configuration
    DEFAULT_TARGET_SECONDS = 60
    MAX_TARGET_SECONDS = 300
    MIN_TARGET_SECONDS = 10
    
    # AI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    WHISPER_MODEL = "tiny"  # Options: tiny, base, small, medium, large
    LLM_MODEL = "gpt-4"
    
    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = "logs/video_summarizer.log"
    ERROR_LOG_FILE = "logs/errors.log"
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS = 100
    RATE_LIMIT_WINDOW = 3600  # 1 hour in seconds
    
    # Security
    PASSWORD_MIN_LENGTH = 6
    PASSWORD_MAX_LENGTH = 128
    
    @classmethod
    def get_database_url(cls) -> str:
        """Get the database URL with proper formatting."""
        return cls.DATABASE_URL
    
    @classmethod
    def get_cors_origins(cls) -> list:
        """Get CORS origins from environment or default."""
        origins = os.getenv("CORS_ORIGINS")
        if origins:
            return [origin.strip() for origin in origins.split(",")]
        return cls.CORS_ORIGINS
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate that all required configuration is present."""
        required_vars = ["JWT_SECRET"]
        missing_vars = []
        
        for var in required_vars:
            if not getattr(cls, var) or getattr(cls, var) == "your-secret-key-change-in-production":
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing or invalid configuration: {', '.join(missing_vars)}")
        
        return True

# Create settings instance
settings = Settings()


