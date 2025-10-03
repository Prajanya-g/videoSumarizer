"""
Pydantic models for the video summarizer API.
"""

from pydantic import BaseModel
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime

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

class JobRequest(BaseModel):
    """Request model for job creation."""
    pass  # Currently using file upload instead

class JobResponse(BaseModel):
    """Response model for job status."""
    job_id: str
    status: JobStatus
    message: Optional[str] = None
    progress: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    error: Optional[str] = None

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

