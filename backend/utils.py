"""
Utility functions for the video summarizer.
"""

import os
import hashlib
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import mimetypes

logger = logging.getLogger(__name__)

def get_file_hash(file_path: str) -> str:
    """Calculate MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        logger.error(f"Failed to calculate file hash: {str(e)}")
        return ""

def get_file_size(file_path: str) -> int:
    """Get file size in bytes."""
    try:
        return os.path.getsize(file_path)
    except OSError:
        return 0

def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"

def format_file_size(size_bytes: int) -> str:
    """Format file size in bytes to human-readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def is_video_file(file_path: str) -> bool:
    """Check if file is a video based on MIME type."""
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type and mime_type.startswith('video/')

def is_audio_file(file_path: str) -> bool:
    """Check if file is an audio based on MIME type."""
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type and mime_type.startswith('audio/')

def get_media_info(file_path: str) -> Dict[str, Any]:
    """Get basic media file information."""
    try:
        stat = os.stat(file_path)
        return {
            "path": file_path,
            "name": Path(file_path).name,
            "size": stat.st_size,
            "size_formatted": format_file_size(stat.st_size),
            "mime_type": mimetypes.guess_type(file_path)[0],
            "is_video": is_video_file(file_path),
            "is_audio": is_audio_file(file_path),
            "modified": stat.st_mtime
        }
    except Exception as e:
        logger.error(f"Failed to get media info: {str(e)}")
        return {}

def ensure_directory(path: str) -> bool:
    """Ensure directory exists, create if necessary."""
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {path}: {str(e)}")
        return False

def safe_filename(filename: str) -> str:
    """Create a safe filename by removing/replacing invalid characters."""
    import re
    # Remove or replace invalid characters
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    safe_name = safe_name.strip(' .')
    # Ensure it's not empty
    if not safe_name:
        safe_name = "unnamed"
    return safe_name

def get_supported_formats() -> Dict[str, list]:
    """Get lists of supported file formats."""
    return {
        "video": [
            "mp4", "avi", "mov", "mkv", "webm", "flv", "wmv", "m4v",
            "3gp", "ogv", "ts", "mts", "m2ts"
        ],
        "audio": [
            "mp3", "wav", "m4a", "aac", "ogg", "flac", "wma", "opus"
        ]
    }

def validate_file_upload(filename: str, file_size: int, max_size: int = 500 * 1024 * 1024) -> Dict[str, Any]:
    """
    Validate uploaded file.
    
    Args:
        filename: Name of the uploaded file
        file_size: Size of the file in bytes
        max_size: Maximum allowed file size in bytes (default: 500MB)
    
    Returns:
        Dict with validation result
    """
    result = {
        "valid": True,
        "errors": [],
        "warnings": []
    }
    
    # Check file extension
    if not filename or '.' not in filename:
        result["valid"] = False
        result["errors"].append("No file extension found")
        return result
    
    extension = filename.lower().split('.')[-1]
    supported_formats = get_supported_formats()
    all_supported = supported_formats["video"] + supported_formats["audio"]
    
    if extension not in all_supported:
        result["valid"] = False
        result["errors"].append(f"Unsupported file format: {extension}")
        return result
    
    # Check file size
    if file_size > max_size:
        result["valid"] = False
        result["errors"].append(f"File too large: {format_file_size(file_size)} (max: {format_file_size(max_size)})")
        return result
    
    if file_size > max_size * 0.8:  # Warning at 80% of max size
        result["warnings"].append(f"Large file: {format_file_size(file_size)}")
    
    return result

def cleanup_old_files(directory: str, max_age_hours: int = 24) -> int:
    """
    Clean up old files in a directory.
    
    Args:
        directory: Directory to clean up
        max_age_hours: Maximum age in hours before deletion
    
    Returns:
        Number of files deleted
    """
    import time
    
    deleted_count = 0
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    
    try:
        for file_path in Path(directory).rglob('*'):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_seconds:
                    file_path.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted old file: {file_path}")
    except Exception as e:
        logger.error(f"Failed to cleanup old files: {str(e)}")
    
    return deleted_count

def get_system_info() -> Dict[str, Any]:
    """Get system information for debugging."""
    import platform
    import psutil
    
    try:
        return {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "memory_available": psutil.virtual_memory().available,
            "disk_usage": psutil.disk_usage('/').percent
        }
    except Exception as e:
        logger.error(f"Failed to get system info: {str(e)}")
        return {}

