"""
FastAPI main application for video summarizer service.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form  # type: ignore
from fastapi.middleware.cors import CORSMiddleware  # type: ignore
from fastapi.staticfiles import StaticFiles  # type: ignore
from fastapi.responses import FileResponse  # type: ignore
import uvicorn  # type: ignore
import os
import uuid
import json
import aiofiles  # type: ignore
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv
from backend.pipeline import VideoSummarizerPipeline
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="Video Summarizer API", version="1.0.0")

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files from data/jobs directory
app.mount("/jobs", StaticFiles(directory="data/jobs"), name="jobs")

# In-memory job state
job_states: Dict[str, Dict[str, Any]] = {}

def get_job_dir(job_id: str) -> Path:
    """Get the directory for a specific job."""
    job_dir = Path(f"data/jobs/{job_id}")
    job_dir.mkdir(parents=True, exist_ok=True)
    return job_dir

async def save_job_state(job_id: str, state: Dict[str, Any]):
    """Save job state to memory and disk."""
    job_states[job_id] = state
    job_dir = get_job_dir(job_id)
    async with aiofiles.open(job_dir / "state.json", "w") as f:
        await f.write(json.dumps(state, indent=2))

def load_job_state(job_id: str) -> Optional[Dict[str, Any]]:
    """Load job state from disk."""
    if job_id in job_states:
        return job_states[job_id]
    
    job_dir = get_job_dir(job_id)
    state_file = job_dir / "state.json"
    if state_file.exists():
        try:
            with open(state_file, "r") as f:
                content = f.read().strip()
                if content:  # Check if file is not empty
                    state = json.loads(content)
                    job_states[job_id] = state
                    return state
        except json.JSONDecodeError as e:
            print(f"Invalid JSON in state file {state_file}: {e}")
            # Return a default state if JSON is corrupted
            return {"status": "unknown", "error": "Corrupted state file"}
    return None

async def process_video_background(job_id: str, target_seconds: int):
    """Background task to process video through the pipeline."""
    try:
        print(f"\n🎬 Background processing started for job: {job_id}")
        
        # Update status to processing
        job_state = load_job_state(job_id)
        if job_state:
            job_state["status"] = "processing"
            job_state["updated_at"] = datetime.now().isoformat()
            await save_job_state(job_id, job_state)
            print("📝 Job status updated to 'processing'")
        
        # Initialize and run the pipeline
        print("🔧 Initializing video processing pipeline...")
        pipeline = VideoSummarizerPipeline()
        await pipeline.run(job_id, target_seconds)
        
        # Update status to done
        job_state = load_job_state(job_id)
        if job_state:
            job_state["status"] = "done"
            job_state["updated_at"] = datetime.now().isoformat()
            await save_job_state(job_id, job_state)
            print(f"✅ Job {job_id} completed successfully!")
            
    except Exception as e:
        print(f"\n❌ Background processing failed for job {job_id}: {str(e)}")
        # Update status to failed
        job_state = load_job_state(job_id)
        if job_state:
            job_state["status"] = "failed"
            job_state["error"] = str(e)
            job_state["updated_at"] = datetime.now().isoformat()
            await save_job_state(job_id, job_state)
            print("📝 Job status updated to 'failed'")

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Video Summarizer API is running"}

@app.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    target_seconds: int = Form(default=60)
):
    """
    Upload a video file and start the summarization process.
    """
    if not file.content_type or not file.content_type.startswith('video/'):
        raise HTTPException(status_code=400, detail="File must be a video")
    
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    try:
        # Create job directory
        job_dir = get_job_dir(job_id)
        
        # Save uploaded file
        input_path = job_dir / "input.mp4"
        async with aiofiles.open(input_path, "wb") as buffer:
            content = await file.read()
            await buffer.write(content)
        
        # Initialize job state
        job_state = {
            "job_id": job_id,
            "status": "uploaded",
            "target_seconds": target_seconds,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "files": {
                "input": str(input_path),
                "video_url": f"/jobs/{job_id}/highlights.mp4",
                "thumbnail_url": f"/jobs/{job_id}/thumb.jpg",
                "srt_url": f"/jobs/{job_id}/transcript.srt"
            }
        }
        
        await save_job_state(job_id, job_state)
        
        # Start background processing pipeline
        print(f"\n🚀 Starting background processing for job: {job_id}")
        # Store task to prevent garbage collection
        _background_task = asyncio.create_task(process_video_background(job_id, target_seconds))
        # Don't store task in job_state as it's not JSON serializable
        # The task will run in background and update job_state separately
        
        # Don't await the task here - let it run in background
        print(f"✅ Background task created for job: {job_id}")
        
        return {"job_id": job_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/result/{job_id}")
async def get_result(job_id: str):
    """
    Get the result payload for a completed job.
    """
    job_state = load_job_state(job_id)
    if not job_state:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check if job is completed
    if job_state["status"] != "done":
        return {
            "status": job_state["status"],
            "message": "Job still processing"
        }
    
    # Load jump_to.json if it exists
    job_dir = get_job_dir(job_id)
    jump_to_file = job_dir / "jump_to.json"
    jump_to = {}
    
    if jump_to_file.exists():
        async with aiofiles.open(jump_to_file, "r") as f:
            content = await f.read()
            jump_to = json.loads(content)
    
    return {
        "status": "done",
        "video_url": job_state["files"]["video_url"],
        "jump_to": jump_to,
        "thumbnail_url": job_state["files"]["thumbnail_url"],
        "srt_url": job_state["files"]["srt_url"]
    }

@app.get("/jobs/{job_id}/highlights.mp4")
async def serve_highlights_video(job_id: str):
    """Serve the highlights video file."""
    job_dir = get_job_dir(job_id)
    video_path = job_dir / "highlights.mp4"
    
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Highlights video not found")
    
    return FileResponse(
        video_path,
        media_type='video/mp4',
        filename=f"highlights_{job_id}.mp4"
    )

@app.get("/jobs/{job_id}/thumb.jpg")
async def serve_thumbnail(job_id: str):
    """Serve the thumbnail image."""
    job_dir = get_job_dir(job_id)
    thumb_path = job_dir / "thumb.jpg"
    
    if not thumb_path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    
    return FileResponse(
        thumb_path,
        media_type='image/jpeg',
        filename=f"thumb_{job_id}.jpg"
    )

@app.get("/jobs/{job_id}/transcript.srt")
async def serve_transcript(job_id: str):
    """Serve the transcript SRT file."""
    job_dir = get_job_dir(job_id)
    srt_path = job_dir / "transcript.srt"
    
    if not srt_path.exists():
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    return FileResponse(
        srt_path,
        media_type='text/plain',
        filename=f"transcript_{job_id}.srt"
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
