"""
SQLAlchemy models for the video summarizer database.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum
from backend.database import Base

class JobStatus(str, Enum):
    """Job processing status."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    TRANSCRIBING = "transcribing"
    RANKING = "ranking"
    SELECTING = "selecting"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"

class User(Base):
    """User model for authentication and job ownership."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship to jobs
    jobs = relationship("Job", back_populates="user", cascade="all, delete-orphan")

class Job(Base):
    """Job model for video processing tasks."""
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=True)
    target_seconds = Column(Integer, nullable=False)
    status = Column(SQLEnum(JobStatus), default=JobStatus.UPLOADED, nullable=False)
    
    # File paths
    input_file_path = Column(String(500), nullable=True)
    audio_file_path = Column(String(500), nullable=True)
    transcript_file_path = Column(String(500), nullable=True)
    transcript_srt_path = Column(String(500), nullable=True)
    highlights_file_path = Column(String(500), nullable=True)
    thumbnail_file_path = Column(String(500), nullable=True)
    jump_to_file_path = Column(String(500), nullable=True)
    result_file_path = Column(String(500), nullable=True)
    
    # Metadata
    original_filename = Column(String(255), nullable=True)
    original_duration = Column(Integer, nullable=True)  # in seconds
    summary_duration = Column(Integer, nullable=True)   # in seconds
    compression_ratio = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Error information
    error_message = Column(Text, nullable=True)
    
    # Relationship to user
    user = relationship("User", back_populates="jobs")
