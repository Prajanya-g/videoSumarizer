"""
FastAPI main application for video summarizer service.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
import json
import aiofiles
import asyncio
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from backend.pipeline import VideoSummarizerPipeline
from backend.database import get_db, create_tables
from backend.services import UserService, JobService
from backend.models import UserCreate, UserResponse, UserLogin, UserUpdate, UserDelete, JobCreate, JobUpdate, JobDelete, JobResponse, JobListQuery
from backend.schemas import JobStatus, User
from backend.auth import create_access_token, get_user_from_token
from sqlalchemy.orm import Session
from backend.logging_config import setup_logging, get_logger
from backend.config import settings

# Set up logging
setup_logging()
logger = get_logger(__name__)

# Constants
USER_NOT_FOUND_MESSAGE = "User not found"

# Initialize database tables
create_tables()

app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    contact={
        "name": settings.API_CONTACT_NAME,
        "email": settings.API_CONTACT_EMAIL,
    },
    license_info={
        "name": settings.API_LICENSE_NAME,
        "url": settings.API_LICENSE_URL,
    },
    servers=[
        {
            "url": f"http://localhost:{settings.PORT}",
            "description": "Development server"
        },
        {
            "url": "https://api.videosummarizer.com",
            "description": "Production server"
        }
    ]
)

# Security
security = HTTPBearer()

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files from data/jobs directory
app.mount("/files", StaticFiles(directory="data/jobs"), name="files")

# Authentication helper functions
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Get current authenticated user from JWT token."""
    token = credentials.credentials
    user_info = get_user_from_token(token)
    
    user = UserService.get_user_by_id(db, user_info["user_id"])
    if not user:
        raise HTTPException(status_code=401, detail=USER_NOT_FOUND_MESSAGE)
    
    return user

def get_job_dir(job_id: str) -> Path:
    """Get the directory for a specific job."""
    job_dir = Path(f"data/jobs/{job_id}")
    job_dir.mkdir(parents=True, exist_ok=True)
    return job_dir

# Old job state functions removed - now using database

async def process_video_background(job_id: int, target_seconds: int):
    """Background task to process video through the pipeline."""
    from backend.database import SessionLocal
    
    db = SessionLocal()
    try:
        logger.info(f"Background processing started for job: {job_id}")
        
        # Update status to processing
        JobService.update_job_status(db, job_id, JobStatus.PROCESSING)
        logger.info("Job status updated to 'processing'")
        
        # Initialize and run the enhanced AI pipeline
        logger.info("Initializing AI-powered video processing pipeline...")
        pipeline = VideoSummarizerPipeline(job_id, db)
        await pipeline.run(target_seconds)
        
        logger.info(f"AI-powered job {job_id} completed successfully!")
            
    except Exception as e:
        logger.error(f"Background processing failed for job {job_id}: {str(e)}")
        # Update status to failed
        JobService.update_job_status(db, job_id, JobStatus.FAILED, str(e))
        logger.error("Job status updated to 'failed'")
    finally:
        db.close()

@app.get(
    "/",
    summary="Health Check",
    description="Check if the API is running and healthy",
    response_description="API status information",
    tags=["Health"]
)
async def root():
    """
    Health check endpoint to verify API availability.
    
    Returns basic information about the API status and version.
    """
    return {
        "message": "Video Summarizer API is running",
        "version": "1.0.0",
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

# Authentication endpoints
@app.post(
    "/register",
    response_model=dict,
    summary="Register a new user",
    description="Create a new user account and return JWT token for authentication",
    response_description="User registration response with JWT token",
    status_code=status.HTTP_201_CREATED,
    tags=["Authentication"]
)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account.
    
    Creates a new user with the provided email, password, and full name.
    Returns a JWT token that can be used for authenticated requests.
    
    - **email**: Valid email address (must be unique)
    - **password**: Password (minimum 6 characters)
    - **full_name**: User's full name
    
    Returns:
    - **user**: User information (id, email, full_name, created_at)
    - **access_token**: JWT token for authentication
    - **token_type**: Token type (always "bearer")
    """
    # Check if user already exists
    existing_user = UserService.get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    try:
        user = UserService.create_user(db, user_data)
        access_token = create_access_token(int(user.id), str(user.email))  # type: ignore
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserResponse.from_orm(user)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post(
    "/login",
    response_model=dict,
    summary="Login user",
    description="Authenticate user with email and password, return JWT token",
    response_description="User login response with JWT token",
    status_code=status.HTTP_200_OK,
    tags=["Authentication"]
)
async def login_user(login_data: UserLogin, db: Session = Depends(get_db)):
    """
    Login an existing user.
    
    Authenticates a user with their email and password.
    Returns a JWT token that can be used for authenticated requests.
    
    - **email**: User's email address
    - **password**: User's password
    
    Returns:
    - **user**: User information (id, email, full_name, created_at)
    - **access_token**: JWT token for authentication
    - **token_type**: Token type (always "bearer")
    """
    user = UserService.authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = create_access_token(int(user.id), str(user.email))  # type: ignore
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user)
    }

@app.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Retrieve the profile information of the currently authenticated user",
    response_description="Current user's profile information",
    status_code=status.HTTP_200_OK,
    tags=["Authentication"]
)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user profile.
    
    Returns the profile information of the currently authenticated user.
    Requires a valid JWT token in the Authorization header.
    
    Returns:
    - **id**: User ID
    - **email**: User's email address
    - **full_name**: User's full name
    - **created_at**: Account creation timestamp
    """
    return UserResponse.from_orm(current_user)

@app.put(
    "/me",
    response_model=UserResponse,
    summary="Update user profile",
    description="Update the profile information of the currently authenticated user",
    response_description="Updated user profile information",
    status_code=status.HTTP_200_OK,
    tags=["Authentication"]
)
async def update_user_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user profile.
    
    Updates the profile information of the currently authenticated user.
    Requires a valid JWT token in the Authorization header.
    
    - **full_name**: New full name (optional)
    - **email**: New email address (optional, must be unique)
    
    Returns:
    - **id**: User ID
    - **email**: Updated email address
    - **full_name**: Updated full name
    - **created_at**: Account creation timestamp
    """
    try:
        updated_user = UserService.update_user(db, int(current_user.id), user_data)  # type: ignore
        if not updated_user:
            raise HTTPException(status_code=404, detail=USER_NOT_FOUND_MESSAGE)
        return UserResponse.from_orm(updated_user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")

@app.delete("/me")
async def delete_user_account(
    delete_data: UserDelete,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete current user account and all their jobs."""
    if not delete_data.confirm:
        raise HTTPException(status_code=400, detail="Account deletion requires confirmation")
    
    try:
        success = UserService.delete_user(db, int(current_user.id))  # type: ignore
        if not success:
            raise HTTPException(status_code=404, detail=USER_NOT_FOUND_MESSAGE)
        return {"message": "Account deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")

@app.post("/upload", response_model=JobResponse)
async def upload_video(
    file: UploadFile = File(...),
    target_seconds: int = Form(default=60),
    title: str = Form(default=None),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a video file and start the summarization process.
    """
    if not file.content_type or not file.content_type.startswith('video/'):
        raise HTTPException(status_code=400, detail="File must be a video")
    
    try:
        # Create job in database
        job_data = JobCreate(title=title, target_seconds=target_seconds)
        job = JobService.create_job(db, current_user.id, job_data, file.filename or "unknown")
        
        # Create job directory
        job_dir = get_job_dir(str(job.id))
        
        # Save uploaded file
        input_path = job_dir / "input.mp4"
        async with aiofiles.open(input_path, "wb") as buffer:
            content = await file.read()
            await buffer.write(content)
        
        job_id: int = job.id  # type: ignore # Get the actual integer value
        
        # Update job with file paths
        JobService.update_job_file_paths(db, job_id, {
            "input_file_path": str(input_path)
        })
        
        # Start background processing pipeline
        logger.info(f"Starting background processing for job: {job_id}")
        _background_task = asyncio.create_task(process_video_background(job_id, target_seconds))
        logger.info(f"Background task created for job: {job_id}")
        
        # Return job response with URLs
        return JobService.get_job_with_urls(db, job_id)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get(
    "/jobs",
    response_model=List[JobResponse],
    summary="Get user's jobs",
    description="Retrieve all jobs for the current user with optional filtering and pagination",
    response_description="List of user's jobs",
    status_code=status.HTTP_200_OK,
    tags=["Jobs"]
)
async def get_user_jobs(
    limit: int = 10,
    offset: int = 0,
    q: Optional[str] = None,
    status: Optional[str] = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all jobs for the current user with optional filtering and pagination.
    
    Query parameters:
    - **limit**: Maximum number of jobs to return (default: 10, max: 100)
    - **offset**: Number of jobs to skip for pagination (default: 0)
    - **q**: Search query for job title or filename (optional)
    - **status**: Filter by job status - uploaded, processing, completed, failed (optional)
    
    Returns:
    - List of job objects with metadata and URLs
    - Each job includes: id, title, status, created_at, file paths, etc.
    """
    query_params = JobListQuery(
        limit=limit,
        offset=offset,
        q=q,
        status=status
    )
    jobs = JobService.get_user_jobs(db, current_user.id, query_params)
    return [JobService.get_job_with_urls(db, job.id) for job in jobs]  # type: ignore

@app.put("/jobs/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: int,
    job_data: JobUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a job (title or target_seconds).
    """
    try:
        updated_job = JobService.update_job(db, job_id, current_user.id, job_data)
        if not updated_job:
            raise HTTPException(status_code=404, detail="Job not found or access denied")
        return JobService.get_job_with_urls(db, job_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")

@app.delete("/jobs/{job_id}")
async def delete_job(
    job_id: int,
    delete_data: JobDelete,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a job and its associated files.
    """
    if not delete_data.confirm:
        raise HTTPException(status_code=400, detail="Job deletion requires confirmation")
    
    try:
        success = JobService.delete_job(db, job_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Job not found or access denied")
        return {"message": "Job deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")

@app.get("/result/{job_id}")
async def get_result(job_id: int, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Get the result payload for a completed job.
    """
    job = JobService.get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check if user owns this job
    if job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if job is completed
    if job.status.value != JobStatus.COMPLETED.value:
        return {
            "status": job.status.value,
            "message": "Job still processing"
        }
    
    # Load jump_to.json if it exists
    job_dir = get_job_dir(str(job_id))
    jump_to_file = job_dir / "jump_to.json"
    jump_to = {}
    
    if jump_to_file.exists():
        async with aiofiles.open(jump_to_file, "r") as f:
            content = await f.read()
            jump_to = json.loads(content)
    
    return {
        "status": "done",
        "video_url": f"/files/{job_id}/highlights.mp4",
        "jump_to": jump_to,
        "thumbnail_url": f"/files/{job_id}/thumb.jpg",
        "srt_url": f"/files/{job_id}/transcript.srt"
    }

@app.get("/files/{job_id}/highlights.mp4")
async def serve_highlights_video(job_id: int):
    """Serve the highlights video file."""
    job_dir = get_job_dir(str(job_id))
    video_path = job_dir / "highlights.mp4"
    
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Highlights video not found")
    
    return FileResponse(
        video_path,
        media_type='video/mp4',
        filename=f"highlights_{job_id}.mp4"
    )

@app.get("/files/{job_id}/thumb.jpg")
async def serve_thumbnail(job_id: int):
    """Serve the thumbnail image."""
    job_dir = get_job_dir(str(job_id))
    thumb_path = job_dir / "thumb.jpg"
    
    if not thumb_path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    
    return FileResponse(
        thumb_path,
        media_type='image/jpeg',
        filename=f"thumb_{job_id}.jpg"
    )

@app.get("/files/{job_id}/transcript.srt")
async def serve_transcript(job_id: int):
    """Serve the transcript SRT file."""
    job_dir = get_job_dir(str(job_id))
    srt_path = job_dir / "transcript.srt"
    
    if not srt_path.exists():
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    return FileResponse(
        srt_path,
        media_type='text/plain',
        filename=f"transcript_{job_id}.srt"
    )

@app.get("/api/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Get a specific job by ID.
    """
    logger.info(f"Getting job {job_id} for user {current_user.id}")
    
    try:
        job = JobService.get_job_by_id(db, job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Check if user owns this job
        if job.user_id != current_user.id:
            logger.error(f"Access denied: job {job_id} belongs to user {job.user_id}, but current user is {current_user.id}")
            raise HTTPException(status_code=403, detail="Access denied")
        
        logger.info(f"Returning job {job_id} with URLs")
        result = JobService.get_job_with_urls(db, job_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving job: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
