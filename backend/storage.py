"""
Storage utilities for job management and file operations.
"""

import json
import logging
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)

class JobStorage:
    """Storage service for job files and utilities."""
    
    def __init__(self, base_dir: str = "data/jobs"):
        """
        Initialize the storage service.
        
        Args:
            base_dir: Base directory for job storage
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def job_dir(self, job_id: str) -> Path:
        """
        Get the directory path for a specific job.
        
        Args:
            job_id: Unique job identifier
            
        Returns:
            Path to the job directory
        """
        job_path = self.base_dir / job_id
        job_path.mkdir(parents=True, exist_ok=True)
        return job_path
    
    def save_upload(self, file) -> Tuple[str, str]:
        """
        Save an uploaded file and return job info.
        
        Args:
            file: Uploaded file object
            
        Returns:
            Tuple of (job_id, input_path)
        """
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Get job directory
        job_path = self.job_dir(job_id)
        
        # Determine file extension
        file_extension = Path(file.filename).suffix if file.filename else ".mp4"
        input_path = job_path / f"input{file_extension}"
        
        # Save file
        with open(input_path, "wb") as buffer:
            content = file.read()
            buffer.write(content)
        
        logger.info(f"File uploaded: {input_path} (job: {job_id})")
        return job_id, str(input_path)
    
    def write_json(self, path: str, obj: Any) -> None:
        """
        Write an object to a JSON file.
        
        Args:
            path: Path to the JSON file
            obj: Object to serialize to JSON
        """
        try:
            file_path = Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, "w") as f:
                json.dump(obj, f, indent=2, default=str)
            
            logger.debug(f"JSON written: {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to write JSON to {path}: {str(e)}")
            raise
    
    def read_json(self, path: str) -> Optional[Any]:
        """
        Read an object from a JSON file.
        
        Args:
            path: Path to the JSON file
            
        Returns:
            Deserialized object or None if file doesn't exist
        """
        try:
            file_path = Path(path)
            
            if not file_path.exists():
                logger.debug(f"JSON file not found: {file_path}")
                return None
            
            with open(file_path, "r") as f:
                data = json.load(f)
            
            logger.debug(f"JSON read: {file_path}")
            return data
            
        except Exception as e:
            logger.error(f"Failed to read JSON from {path}: {str(e)}")
            return None
    
    def file_exists(self, path: str) -> bool:
        """Check if a file exists."""
        return Path(path).exists()
    
    def get_file_size(self, path: str) -> int:
        """Get file size in bytes."""
        try:
            return Path(path).stat().st_size
        except OSError:
            return 0
    
    def cleanup_job(self, job_id: str) -> None:
        """Clean up job files and directory."""
        try:
            job_path = self.job_dir(job_id)
            if job_path.exists():
                import shutil
                shutil.rmtree(job_path)
                logger.info(f"Job cleaned up: {job_id}")
        except Exception as e:
            logger.error(f"Failed to cleanup job {job_id}: {str(e)}")
    
    def list_jobs(self) -> list:
        """List all job directories."""
        try:
            jobs = []
            for job_dir in self.base_dir.iterdir():
                if job_dir.is_dir():
                    jobs.append(job_dir.name)
            return sorted(jobs, reverse=True)  # Most recent first
        except Exception as e:
            logger.error(f"Failed to list jobs: {str(e)}")
            return []
    
    def get_job_files(self, job_id: str) -> Dict[str, str]:
        """Get all files in a job directory."""
        try:
            job_path = self.job_dir(job_id)
            files = {}
            
            for file_path in job_path.iterdir():
                if file_path.is_file():
                    files[file_path.name] = str(file_path)
            
            return files
        except Exception as e:
            logger.error(f"Failed to get job files for {job_id}: {str(e)}")
            return {}
