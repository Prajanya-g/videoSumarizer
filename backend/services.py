"""
Service layer for database operations.

This module contains the business logic layer that handles all database
operations for users and jobs. It provides a clean interface between
the API endpoints and the database models.
"""

from sqlalchemy.orm import Session
from typing import Optional, List
from backend.schemas import User, Job, JobStatus
from backend.models import UserCreate, UserLogin, UserUpdate, UserDelete, JobCreate, JobUpdate, JobDelete, JobResponse, JobListQuery
from backend.auth import hash_password, verify_password
import os

# =============================================================================
# USER SERVICE - Handles user authentication and profile management
# =============================================================================

class UserService:
    """
    Service class for user-related database operations.
    
    Provides methods for user creation, authentication, profile updates,
    and account management with proper password hashing and validation.
    """
    
    
    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        """
        Create a new user account.
        
        Hashes the password and stores user information in the database.
        
        Args:
            db: Database session
            user_data: User creation data (email, password, full_name)
            
        Returns:
            User: Created user object
            
        Raises:
            IntegrityError: If email already exists
        """
        # Hash password before storing
        hashed_password = hash_password(user_data.password)
        db_user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email."""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """Get user by ID."""
        # Use explicit query to avoid any LIMIT/OFFSET issues
        try:
            return db.query(User).filter(User.id == user_id).one_or_none()
        except Exception:
            # Fallback to raw SQL if ORM query fails
            from sqlalchemy import text
            result = db.execute(text("SELECT * FROM users WHERE id = :user_id"), {"user_id": user_id}).fetchone()
            if result:
                return User(
                    id=result.id,
                    email=result.email,
                    hashed_password=result.hashed_password,
                    full_name=result.full_name,
                    created_at=result.created_at
                )
            return None
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate a user."""
        user = UserService.get_user_by_email(db, email)
        if not user:
            return None
        if not verify_password(password, str(user.hashed_password)):
            return None
        return user
    
    @staticmethod
    def update_user(db: Session, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """Update user profile."""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return None
        
        # Check if email is being changed and if it's already taken
        if user_data.email and user_data.email != user.email:
            existing_user = UserService.get_user_by_email(db, user_data.email)
            if existing_user:
                raise ValueError("Email already registered")
        
        # Update fields using SQLAlchemy update
        update_data = {}
        if user_data.full_name is not None:
            update_data['full_name'] = user_data.full_name
        if user_data.email is not None:
            update_data['email'] = user_data.email
        
        if update_data:
            db.query(User).filter(User.id == user_id).update(update_data)
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        """Delete user and all their jobs."""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return False
        
        # Delete user (cascade will delete all jobs)
        db.delete(user)
        db.commit()
        return True

# =============================================================================
# JOB SERVICE - Handles video processing job management
# =============================================================================

class JobService:
    """
    Service class for job-related database operations.
    
    Provides methods for job creation, status updates, file path management,
    and job listing with filtering and pagination support.
    """
    
    @staticmethod
    def create_job(db: Session, user_id: int, job_data: JobCreate, original_filename: Optional[str] = None) -> Job:
        """
        Create a new video processing job.
        
        Initializes a job record with UPLOADED status and user ownership.
        
        Args:
            db: Database session
            user_id: ID of the user creating the job
            job_data: Job configuration (title, target_seconds)
            original_filename: Name of the uploaded file
            
        Returns:
            Job: Created job object
        """
        db_job = Job(
            user_id=user_id,
            title=job_data.title,
            target_seconds=job_data.target_seconds,
            original_filename=original_filename,
            status=JobStatus.UPLOADED  # Initial status
        )
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        return db_job
    
    @staticmethod
    def get_job_by_id(db: Session, job_id: int) -> Optional[Job]:
        """Get job by ID."""
        return db.query(Job).filter(Job.id == job_id).first()
    
    @staticmethod
    def get_user_jobs(db: Session, user_id: int, query_params: Optional[JobListQuery] = None) -> List[Job]:
        """Get all jobs for a user with optional filtering and pagination."""
        query = db.query(Job).filter(Job.user_id == user_id)
        
        if query_params:
            # Search by title or original filename
            if query_params.q:
                search_term = f"%{query_params.q}%"
                query = query.filter(
                    (Job.title.ilike(search_term)) | (Job.original_filename.ilike(search_term))
                )
            
            # Filter by status
            if query_params.status:
                query = query.filter(Job.status == query_params.status)
        
        # Apply ordering first, then pagination
        query = query.order_by(Job.created_at.desc())
        
        if query_params:
            # Apply pagination after ordering
            if query_params.offset:
                query = query.offset(query_params.offset)
            if query_params.limit:
                query = query.limit(query_params.limit)
        
        return query.all()
    
    @staticmethod
    def update_job(db: Session, job_id: int, user_id: int, job_data: JobUpdate) -> Optional[Job]:
        """Update a job."""
        job = db.query(Job).filter(Job.id == job_id, Job.user_id == user_id).first()
        if not job:
            return None
        
        # Update fields using SQLAlchemy update
        update_data = {}
        if job_data.title is not None:
            update_data['title'] = job_data.title
        if job_data.target_seconds is not None:
            update_data['target_seconds'] = job_data.target_seconds
        
        if update_data:
            db.query(Job).filter(Job.id == job_id).update(update_data)
        db.commit()
        db.refresh(job)
        return job
    
    @staticmethod
    def delete_job(db: Session, job_id: int, user_id: int) -> bool:
        """Delete a job and its files."""
        job = db.query(Job).filter(Job.id == job_id, Job.user_id == user_id).first()
        if not job:
            return False
        
        # Delete job (files will be cleaned up by the system)
        db.delete(job)
        db.commit()
        return True
    
    @staticmethod
    def update_job_status(db: Session, job_id: int, status: JobStatus, error_message: Optional[str] = None) -> Optional[Job]:
        """Update job status."""
        job = JobService.get_job_by_id(db, job_id)
        if not job:
            return None
        
        # Update status using SQLAlchemy update
        if error_message:
            db.query(Job).filter(Job.id == job_id).update({
                Job.status: status.value,
                Job.error_message: error_message
            })
        else:
            db.query(Job).filter(Job.id == job_id).update({
                Job.status: status.value
            })
        
        db.commit()
        db.refresh(job)
        return job
    
    @staticmethod
    def update_job_file_paths(db: Session, job_id: int, file_paths: dict) -> Optional[Job]:
        """Update job file paths."""
        job = JobService.get_job_by_id(db, job_id)
        if not job:
            return None
        
        # Update file paths using SQLAlchemy update
        update_data = {}
        for field, path in file_paths.items():
            if hasattr(job, field):
                update_data[field] = path
        
        if update_data:
            db.query(Job).filter(Job.id == job_id).update(update_data)
        db.commit()
        db.refresh(job)
        return job
    
    @staticmethod
    def update_job_metadata(db: Session, job_id: int, metadata: dict) -> Optional[Job]:
        """Update job metadata (duration, compression ratio, etc.)."""
        job = JobService.get_job_by_id(db, job_id)
        if not job:
            return None
        
        # Update metadata fields using SQLAlchemy update
        update_data = {}
        for field, value in metadata.items():
            if hasattr(job, field):
                update_data[field] = value
        
        if update_data:
            db.query(Job).filter(Job.id == job_id).update(update_data)
        db.commit()
        db.refresh(job)
        return job
    
    @staticmethod
    def get_job_with_urls(db: Session, job_id: int) -> Optional[JobResponse]:
        """Get job with computed URLs."""
        job = JobService.get_job_by_id(db, job_id)
        if not job:
            return None
        
        # Convert to response model with URLs
        job_response = JobResponse.from_orm(job)
        
        # Compute URLs based on file paths
        highlights_path = getattr(job, 'highlights_file_path', None)
        if highlights_path and os.path.exists(str(highlights_path)):
            job_response.video_url = f"/files/{job_id}/highlights.mp4"
        
        thumbnail_path = getattr(job, 'thumbnail_file_path', None)
        if thumbnail_path and os.path.exists(str(thumbnail_path)):
            job_response.thumbnail_url = f"/files/{job_id}/thumb.jpg"
        
        transcript_path = getattr(job, 'transcript_srt_path', None)
        if transcript_path and os.path.exists(str(transcript_path)):
            job_response.srt_url = f"/files/{job_id}/transcript.srt"
        
        return job_response
