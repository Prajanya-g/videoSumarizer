"""
Pydantic models for the video summarizer API.

This module defines all request/response models used in the FastAPI endpoints.
These models handle data validation, serialization, and API documentation.
"""

from pydantic import BaseModel, EmailStr
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from backend.schemas import JobStatus

# =============================================================================
# USER MODELS - Handle user authentication and profile management
# =============================================================================

class UserCreate(BaseModel):
    """
    Model for user registration requests.
    
    Validates email format and ensures password is provided.
    Full name is optional for user convenience.
    """
    email: EmailStr  # Validated email format
    password: str  # Plain text password (will be hashed)
    full_name: Optional[str] = None  # Optional display name

class UserResponse(BaseModel):
    """
    Model for user data returned in API responses.
    
    Excludes sensitive information like passwords.
    Used for profile display and authentication responses.
    """
    id: int  # Unique user identifier
    email: str  # User's email address
    full_name: Optional[str]  # Display name (may be None)
    created_at: datetime  # Account creation timestamp
    
    class Config:
        from_attributes = True  # Enable ORM model conversion

class UserLogin(BaseModel):
    """
    Model for user login requests.
    
    Requires email and password for authentication.
    """
    email: EmailStr  # User's email address
    password: str  # Plain text password for verification

class UserUpdate(BaseModel):
    """
    Model for user profile updates.
    
    All fields are optional - only provided fields will be updated.
    Email updates require uniqueness validation.
    """
    full_name: Optional[str] = None  # New display name
    email: Optional[EmailStr] = None  # New email (must be unique)

class UserDelete(BaseModel):
    """
    Model for user account deletion confirmation.
    
    Requires explicit confirmation to prevent accidental deletions.
    """
    confirm: bool = False  # Must be True to proceed with deletion

# =============================================================================
# JOB MODELS - Handle video processing job management
# =============================================================================

class JobRequest(BaseModel):
    """
    Legacy model for job creation requests.
    
    Currently unused - job creation is handled via file upload endpoint.
    Kept for potential future use or API consistency.
    """
    pass  # Currently using file upload instead

class JobResponse(BaseModel):
    """
    Model for job data returned in API responses.
    
    Includes all job metadata, processing status, and computed file URLs.
    Used for job listing, details, and status updates.
    """
    # Core job identification
    id: int  # Unique job identifier
    user_id: int  # Owner of this job
    
    # Job configuration
    title: Optional[str]  # User-defined job title
    target_seconds: int  # Desired summary duration in seconds
    status: JobStatus  # Current processing state
    
    # File information
    original_filename: Optional[str]  # Name of uploaded file
    original_duration: Optional[int]  # Original video duration (seconds)
    summary_duration: Optional[int]  # Final summary duration (seconds)
    compression_ratio: Optional[str]  # Compression ratio (e.g., "3.2x")
    
    # Timestamps
    created_at: datetime  # Job creation time
    updated_at: datetime  # Last modification time
    
    # Error handling
    error_message: Optional[str] = None  # Error details if processing failed
    
    # Computed file URLs for client access
    video_url: Optional[str] = None  # URL to highlights video
    thumbnail_url: Optional[str] = None  # URL to thumbnail image
    srt_url: Optional[str] = None  # URL to SRT subtitle file
    
    class Config:
        from_attributes = True  # Enable ORM model conversion

class JobCreate(BaseModel):
    """
    Model for creating new video processing jobs.
    
    Used when uploading videos to specify processing parameters.
    """
    title: Optional[str] = None  # Optional user-defined job title
    target_seconds: int  # Required target duration for summary

class JobUpdate(BaseModel):
    """
    Model for updating existing jobs.
    
    Allows modification of job title and target duration.
    All fields are optional - only provided fields will be updated.
    """
    title: Optional[str] = None  # New job title
    target_seconds: Optional[int] = None  # New target duration

class JobDelete(BaseModel):
    """
    Model for job deletion confirmation.
    
    Requires explicit confirmation to prevent accidental deletions.
    """
    confirm: bool = False  # Must be True to proceed with deletion

class JobListQuery(BaseModel):
    """
    Model for job listing query parameters.
    
    Supports pagination, search, and status filtering.
    """
    limit: Optional[int] = 10  # Maximum number of jobs to return
    offset: Optional[int] = 0  # Number of jobs to skip (pagination)
    q: Optional[str] = None  # Search query for title/filename
    status: Optional[str] = None  # Filter by job status

# =============================================================================
# PROCESSING MODELS - Handle video processing pipeline data structures
# =============================================================================

class TranscriptionSegment(BaseModel):
    """
    Individual segment from video transcription.
    
    Represents a single spoken segment with timing and confidence data.
    """
    start: float  # Start time in seconds
    end: float  # End time in seconds
    text: str  # Transcribed text content
    confidence: Optional[float] = None  # Transcription confidence score (0-1)

class TranscriptionResult(BaseModel):
    """
    Complete transcription result from Whisper processing.
    
    Contains all segments and metadata from the transcription process.
    """
    segments: List[TranscriptionSegment]  # All transcribed segments
    full_text: str  # Complete concatenated text
    language: Optional[str] = None  # Detected language code
    duration: float  # Total video duration in seconds

class RankedSegment(BaseModel):
    """
    Transcript segment with AI-generated ranking score.
    
    Used during the LLM ranking phase to score segment importance.
    """
    start: float  # Start time in seconds
    end: float  # End time in seconds
    text: str  # Segment text content
    score: float  # AI-generated importance score
    rank: int  # Rank position (1 = most important)

class SelectedSegment(BaseModel):
    """
    Final segment selected for the summary video.
    
    Represents segments that will be included in the final highlight video.
    """
    start: float  # Start time in seconds
    end: float  # End time in seconds
    text: str  # Segment text content
    score: float  # Importance score
    duration: float  # Segment duration in seconds

class SummaryResult(BaseModel):
    """
    Complete summary processing result.
    
    Contains all metadata about the summarization process and results.
    """
    original_duration: float  # Original video duration (seconds)
    summary_duration: float  # Final summary duration (seconds)
    compression_ratio: float  # Compression ratio (original/summary)
    segments: List[SelectedSegment]  # Selected segments for summary
    total_segments: int  # Total number of original segments
    selected_segments: int  # Number of segments selected for summary

class ProcessingStep(BaseModel):
    """
    Individual step in the processing pipeline.
    
    Tracks the status and progress of each processing phase.
    """
    step_name: str  # Name of the processing step
    status: str  # Current status (pending, running, completed, failed)
    progress: float  # Progress percentage (0-100)
    start_time: Optional[datetime] = None  # Step start time
    end_time: Optional[datetime] = None  # Step completion time
    error: Optional[str] = None  # Error message if step failed

class JobInfo(BaseModel):
    """
    Complete job information with processing details.
    
    Comprehensive model containing all job data and processing status.
    """
    job_id: str  # Unique job identifier
    status: JobStatus  # Current job status
    file_path: Optional[str] = None  # Input file path
    result_path: Optional[str] = None  # Result file path
    original_filename: Optional[str] = None  # Original filename
    created_at: datetime  # Job creation timestamp
    updated_at: datetime  # Last update timestamp
    processing_steps: List[ProcessingStep] = []  # Processing step details
    summary_result: Optional[SummaryResult] = None  # Final summary results
    error: Optional[str] = None  # Error message if processing failed

