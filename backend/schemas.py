"""
SQLAlchemy models for the video summarizer database.

This module defines the core database models for the video summarization service,
including user authentication, job tracking, and file management.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum
from backend.database import Base

class JobStatus(str, Enum):
    """
    Enumeration of possible job processing states.
    
    Tracks the progress of video processing through the pipeline:
    - UPLOADED: Video file uploaded, ready for processing
    - PROCESSING: General processing state (legacy)
    - TRANSCRIBING: Converting audio to text using Whisper
    - RANKING: Using LLM to score and rank transcript segments
    - SELECTING: Choosing best segments based on target duration
    - RENDERING: Creating final highlight video
    - COMPLETED: Processing finished successfully
    - FAILED: Processing encountered an error
    """
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    TRANSCRIBING = "transcribing"
    RANKING = "ranking"
    SELECTING = "selecting"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"

class User(Base):
    """
    User model for authentication and job ownership.
    
    Stores user account information and maintains a one-to-many relationship
    with Job records. When a user is deleted, all their jobs are also deleted.
    """
    __tablename__ = "users"
    
    # Primary key and indexing
    id = Column(Integer, primary_key=True, index=True)
    
    # Authentication fields
    email = Column(String(255), unique=True, index=True, nullable=False)  # Unique email for login
    hashed_password = Column(String(255), nullable=False)  # Bcrypt hashed password
    full_name = Column(String(255), nullable=True)  # Optional display name
    
    # Audit timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship to jobs - cascade delete ensures user's jobs are removed when user is deleted
    jobs = relationship("Job", back_populates="user", cascade="all, delete-orphan")

class Job(Base):
    """
    Job model for video processing tasks.
    
    Tracks individual video processing jobs from upload to completion.
    Each job belongs to a user and contains all file paths and metadata
    generated during the processing pipeline.
    """
    __tablename__ = "jobs"
    
    # Primary key and foreign key relationships
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Owner of this job
    
    # Job configuration
    title = Column(String(255), nullable=True)  # Optional user-defined title
    target_seconds = Column(Integer, nullable=False)  # Desired summary duration
    status = Column(SQLEnum(JobStatus), default=JobStatus.UPLOADED, nullable=False)  # Current processing state
    
    # File paths - stored as strings to allow for flexible storage locations
    input_file_path = Column(String(500), nullable=True)  # Original uploaded video
    audio_file_path = Column(String(500), nullable=True)  # Extracted audio track
    transcript_file_path = Column(String(500), nullable=True)  # JSON transcript data
    transcript_srt_path = Column(String(500), nullable=True)  # SRT subtitle file
    highlights_file_path = Column(String(500), nullable=True)  # Final highlight video
    thumbnail_file_path = Column(String(500), nullable=True)  # Video thumbnail image
    jump_to_file_path = Column(String(500), nullable=True)  # Timestamp mapping for navigation
    result_file_path = Column(String(500), nullable=True)  # Processing result metadata
    
    # Processing metadata
    original_filename = Column(String(255), nullable=True)  # Name of uploaded file
    original_duration = Column(Integer, nullable=True)  # Original video duration in seconds
    summary_duration = Column(Integer, nullable=True)  # Final summary duration in seconds
    compression_ratio = Column(String(50), nullable=True)  # Calculated compression ratio (e.g., "3.2x")
    
    # Audit timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Job creation time
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())  # Last modification time
    
    # Error tracking
    error_message = Column(Text, nullable=True)  # Error details if processing fails
    
    # Relationship back to user
    user = relationship("User", back_populates="jobs")
