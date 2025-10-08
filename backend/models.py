"""
Pydantic models for the video summarizer API.
"""

from pydantic import BaseModel, EmailStr
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from backend.schemas import JobStatus

# User models
class UserCreate(BaseModel):
    """User creation model."""
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserResponse(BaseModel):
    """User response model."""
    id: int
    email: str
    full_name: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    """User login model."""
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    """User update model."""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None

class UserDelete(BaseModel):
    """User deletion confirmation model."""
    confirm: bool = False

class JobRequest(BaseModel):
    """Request model for job creation."""
    pass  # Currently using file upload instead

class JobResponse(BaseModel):
    """Response model for job status."""
    id: int
    user_id: int
    title: Optional[str]
    target_seconds: int
    status: JobStatus
    original_filename: Optional[str]
    original_duration: Optional[int]
    summary_duration: Optional[int]
    compression_ratio: Optional[str]
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None
    
    # File URLs (computed from paths)
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    srt_url: Optional[str] = None
    
    class Config:
        from_attributes = True

class JobCreate(BaseModel):
    """Job creation model."""
    title: Optional[str] = None
    target_seconds: int

class JobUpdate(BaseModel):
    """Job update model."""
    title: Optional[str] = None
    target_seconds: Optional[int] = None

class JobDelete(BaseModel):
    """Job deletion confirmation model."""
    confirm: bool = False

class JobListQuery(BaseModel):
    """Query parameters for job listing."""
    limit: Optional[int] = 10
    offset: Optional[int] = 0
    q: Optional[str] = None  # Search query
    status: Optional[str] = None  # Filter by status

class TranscriptionSegment(BaseModel):
    """Individual transcription segment."""
    start: float
    end: float
    text: str
    confidence: Optional[float] = None

class TranscriptionResult(BaseModel):
    """Complete transcription result."""
    segments: List[TranscriptionSegment]
    full_text: str
    language: Optional[str] = None
    duration: float

class RankedSegment(BaseModel):
    """Segment with ranking score."""
    start: float
    end: float
    text: str
    score: float
    rank: int

class SelectedSegment(BaseModel):
    """Final selected segment for summary."""
    start: float
    end: float
    text: str
    score: float
    duration: float

class SummaryResult(BaseModel):
    """Final summary result."""
    original_duration: float
    summary_duration: float
    compression_ratio: float
    segments: List[SelectedSegment]
    total_segments: int
    selected_segments: int

class ProcessingStep(BaseModel):
    """Individual processing step status."""
    step_name: str
    status: str
    progress: float
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error: Optional[str] = None

class JobInfo(BaseModel):
    """Complete job information."""
    job_id: str
    status: JobStatus
    file_path: Optional[str] = None
    result_path: Optional[str] = None
    original_filename: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    processing_steps: List[ProcessingStep] = []
    summary_result: Optional[SummaryResult] = None
    error: Optional[str] = None

