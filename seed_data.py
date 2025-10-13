#!/usr/bin/env python3
"""
Seed script for Video Summarizer database.

This script creates sample data for testing and demonstration purposes.
Run with: python seed_data.py
"""

import os
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from backend.database import get_db, create_tables
from backend.services import UserService, JobService
from backend.schemas import UserCreate, JobCreate, JobStatus
from backend.models import UserCreate as UserCreateModel, JobCreate as JobCreateModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random

def create_sample_users(db: Session) -> list:
    """Create sample users for testing."""
    users = []
    
    sample_users = [
        {
            "email": "demo@example.com",
            "password": "demo123",
            "full_name": "Demo User"
        },
        {
            "email": "john@example.com", 
            "password": "john123",
            "full_name": "John Doe"
        },
        {
            "email": "jane@example.com",
            "password": "jane123", 
            "full_name": "Jane Smith"
        },
        {
            "email": "admin@example.com",
            "password": "admin123",
            "full_name": "Admin User"
        }
    ]
    
    for user_data in sample_users:
        try:
            user = UserService.create_user(db, UserCreateModel(**user_data))
            users.append(user)
            print(f"✅ Created user: {user.email}")
        except Exception as e:
            print(f"❌ Failed to create user {user_data['email']}: {e}")
    
    return users

def create_sample_jobs(db: Session, users: list) -> list:
    """Create sample jobs for testing."""
    jobs = []
    
    sample_jobs = [
        {
            "title": "Product Launch Presentation",
            "target_seconds": 60,
            "status": JobStatus.COMPLETED,
            "created_at": datetime.now() - timedelta(days=1)
        },
        {
            "title": "Team Meeting Recording", 
            "target_seconds": 120,
            "status": JobStatus.PROCESSING,
            "created_at": datetime.now() - timedelta(hours=2)
        },
        {
            "title": "Conference Talk Highlights",
            "target_seconds": 180,
            "status": JobStatus.COMPLETED,
            "created_at": datetime.now() - timedelta(days=3)
        },
        {
            "title": "Training Video Summary",
            "target_seconds": 90,
            "status": JobStatus.FAILED,
            "created_at": datetime.now() - timedelta(hours=6)
        },
        {
            "title": "Interview Highlights",
            "target_seconds": 150,
            "status": JobStatus.COMPLETED,
            "created_at": datetime.now() - timedelta(days=2)
        }
    ]
    
    for i, job_data in enumerate(sample_jobs):
        try:
            # Assign jobs to different users
            user = users[i % len(users)]
            
            job = JobService.create_job(
                db, 
                user.id, 
                JobCreateModel(title=job_data["title"], target_seconds=job_data["target_seconds"]),
                f"sample_video_{i+1}.mp4"
            )
            
            # Update job status and creation time
            job.status = job_data["status"]
            job.created_at = job_data["created_at"]
            
            # Add some metadata for completed jobs
            if job_data["status"] == JobStatus.COMPLETED:
                job.duration_seconds = random.randint(45, 200)
                job.compression_ratio = round(random.uniform(0.3, 0.8), 2)
            
            db.commit()
            jobs.append(job)
            print(f"✅ Created job: {job.title} for {user.email}")
            
        except Exception as e:
            print(f"❌ Failed to create job {job_data['title']}: {e}")
    
    return jobs

def main():
    """Main seed function."""
    print("🌱 Starting database seeding...")
    
    # Create tables if they don't exist
    create_tables()
    print("✅ Database tables created")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Create sample users
        print("\n👥 Creating sample users...")
        users = create_sample_users(db)
        
        # Create sample jobs
        print("\n📹 Creating sample jobs...")
        jobs = create_sample_jobs(db, users)
        
        print(f"\n🎉 Seeding completed!")
        print(f"   - Created {len(users)} users")
        print(f"   - Created {len(jobs)} jobs")
        print(f"\n📧 Demo login credentials:")
        print(f"   - Email: demo@example.com")
        print(f"   - Password: demo123")
        print(f"   - Email: john@example.com") 
        print(f"   - Password: john123")
        
    except Exception as e:
        print(f"❌ Seeding failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
