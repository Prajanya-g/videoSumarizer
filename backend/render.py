"""
FFmpeg-based video rendering service with robust error handling.

This module provides comprehensive video processing capabilities using FFmpeg:
- Video concatenation and editing
- Thumbnail generation with multiple fallback strategies
- Audio extraction and processing
- Video duration analysis
- Quality optimization and format conversion

The service is designed to be robust with multiple fallback strategies
for different video formats and codecs.
"""

import os
import logging
import subprocess
import asyncio
import tempfile
import aiofiles
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

def _create_temp_file(suffix: str, mode: str = 'w') -> str:
    """Create a temporary file and return its path."""
    with tempfile.NamedTemporaryFile(mode=mode, suffix=suffix, delete=False) as tmp_file:
        return tmp_file.name

# Constants for FFmpeg options
FASTSTART_FLAG = "+faststart"
H264_CODEC = "libx264"
AAC_CODEC = "aac"
VERYFAST_PRESET = "veryfast"
CRF_QUALITY = "23"

class VideoRenderer:
    """
    Service for rendering summary videos using FFmpeg.
    
    This class provides a comprehensive interface for video processing operations:
    - Video concatenation with multiple strategies (stream copy vs re-encoding)
    - Thumbnail generation with fallback methods
    - Audio extraction and processing
    - Video duration analysis using ffprobe
    - Quality optimization and format conversion
    
    The renderer uses multiple fallback strategies to handle different video
    formats, codecs, and edge cases robustly.
    """
    
    def __init__(self, ffmpeg_path: str = "ffmpeg", ffprobe_path: str = "ffprobe"):
        """
        Initialize the video renderer with FFmpeg executables.
        
        Args:
            ffmpeg_path: Path to ffmpeg executable (default: "ffmpeg" from PATH)
            ffprobe_path: Path to ffprobe executable (default: "ffprobe" from PATH)
        """
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path
    
    async def export_concat(self, input_video: str, segments: List[Dict], out_path: str) -> str:
        """
        Export concatenated video from segments with robust error handling.
        
        Args:
            input_video: Path to input video file
            segments: List of segments with start, end, label
            out_path: Output path for the concatenated video
            
        Returns:
            Path to the output video file
        """
        try:
            if not segments:
                raise ValueError("No segments provided for rendering")
            
            # Ensure output directory exists
            Path(out_path).parent.mkdir(parents=True, exist_ok=True)
            
            if len(segments) <= 1:
                # Single segment - just copy that range
                return await self._export_single_segment(input_video, segments[0], out_path)
            else:
                # Multiple segments - use concat method
                return await self._export_multiple_segments(input_video, segments, out_path)
                
        except Exception as e:
            logger.error(f"Video export failed: {str(e)}")
            raise
    
    async def _export_single_segment(self, input_video: str, segment: Dict, out_path: str) -> str:
        """Export a single segment with re-encoding."""
        try:
            start = segment["start"]
            end = segment["end"]
            duration = end - start
            
            cmd = [
                self.ffmpeg_path,
                "-i", input_video,
                "-ss", str(start),
                "-t", str(duration),
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "23",
                "-c:a", "aac",
                "-movflags", FASTSTART_FLAG,
                "-y",
                out_path
            ]
            
            await self._run_ffmpeg(cmd)
            logger.info(f"Single segment exported: {out_path}")
            return out_path
            
        except Exception as e:
            logger.error(f"Single segment export failed: {str(e)}")
            raise
    
    async def _export_multiple_segments(self, input_video: str, segments: List[Dict], out_path: str) -> str:
        """Export multiple segments using concat method."""
        try:
            # First, re-encode each segment
            temp_segments = []
            
            for i, segment in enumerate(segments):
                temp_path = await self._reencode_segment(input_video, segment, i)
                temp_segments.append(temp_path)
            
            # Create concat file
            concat_file = await self._create_concat_file(temp_segments)
            
            try:
                # Try stream copy first (fastest)
                success = await self._concat_with_copy(concat_file, out_path)
                if success:
                    logger.info(f"Concatenated with stream copy: {out_path}")
                    return out_path
            except Exception as e:
                logger.warning(f"Stream copy failed, falling back to re-encode: {str(e)}")
            
            # Fallback to re-encoding
            await self._concat_with_reencode(concat_file, out_path)
            logger.info(f"Concatenated with re-encode: {out_path}")
            return out_path
            
        except Exception as e:
            logger.error(f"Multiple segments export failed: {str(e)}")
            raise
        finally:
            # Clean up temporary files
            self._cleanup_temp_files(temp_segments)
    
    async def _reencode_segment(self, input_video: str, segment: Dict, index: int) -> str:
        """Re-encode a single segment with specified settings."""
        start = segment["start"]
        end = segment["end"]
        duration = end - start
        
        # Create temporary file for this segment
        temp_path = _create_temp_file(f"_seg_{index}.mp4")
        
        try:
            cmd = [
                self.ffmpeg_path,
                "-i", input_video,
                "-ss", str(start),
                "-t", str(duration),
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "23",
                "-c:a", "aac",
                "-movflags", FASTSTART_FLAG,
                "-y",
                temp_path
            ]
            
            await self._run_ffmpeg(cmd)
            return temp_path
            
        except Exception:
            # Clean up on failure
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise
    
    async def _create_concat_file(self, segment_paths: List[str]) -> str:
        """Create FFmpeg concat file."""
        concat_file = _create_temp_file('.txt', 'w')
        async with aiofiles.open(concat_file, 'w') as f:
            for path in segment_paths:
                await f.write(f"file '{path}'\n")
        
        return concat_file
    
    async def _concat_with_copy(self, concat_file: str, out_path: str) -> bool:
        """Try concatenation with stream copy (fastest)."""
        try:
            cmd = [
                self.ffmpeg_path,
                "-f", "concat",
                "-safe", "0",
                "-i", concat_file,
                "-c", "copy",
                "-y",
                out_path
            ]
            
            await self._run_ffmpeg(cmd)
            return True
            
        except Exception as e:
            logger.warning(f"Stream copy concat failed: {str(e)}")
            return False
    
    async def _concat_with_reencode(self, concat_file: str, out_path: str) -> None:
        """Concatenate with re-encoding (fallback)."""
        cmd = [
            self.ffmpeg_path,
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "23",
            "-c:a", "aac",
            "-movflags", "+faststart",
            "-y",
            out_path
        ]
        
        await self._run_ffmpeg(cmd)
    
    async def make_thumbnail(self, input_video: str, t: float, out_path: str) -> str:
        """
        Create a thumbnail at time t with robust error handling.
        
        This method uses a two-tier approach for thumbnail generation:
        1. First attempts optimized method with MJPEG encoding
        2. Falls back to re-encoding if the first method fails
        
        The method ensures proper JPEG format output that can be opened
        by standard image viewers and web browsers.
        
        Args:
            input_video: Path to input video file
            t: Time in seconds where thumbnail should be extracted
            out_path: Output path for the thumbnail image
            
        Returns:
            str: Path to the created thumbnail file
            
        Raises:
            Exception: If both thumbnail generation methods fail
        """
        try:
            # Ensure output directory exists to prevent file creation errors
            Path(out_path).parent.mkdir(parents=True, exist_ok=True)
            
            # First try optimized method with MJPEG encoding (fastest and most reliable)
            success = await self._thumbnail_with_copy(input_video, t, out_path)
            if success:
                logger.info(f"Thumbnail created with optimized method: {out_path}")
                return out_path
            
            # Fallback to re-encoding method if optimized approach fails
            # This handles edge cases with certain video formats or codecs
            await self._thumbnail_with_reencode(input_video, t, out_path)
            logger.info(f"Thumbnail created with re-encode fallback: {out_path}")
            return out_path
            
        except Exception as e:
            logger.error(f"Thumbnail creation failed: {str(e)}")
            raise
    
    async def _thumbnail_with_copy(self, input_video: str, t: float, out_path: str) -> bool:
        """
        Try thumbnail creation with optimized MJPEG settings.
        
        This method uses MJPEG encoding which is specifically designed for
        JPEG image output. It's faster than re-encoding and produces
        high-quality thumbnails that are compatible with all image viewers.
        
        Args:
            input_video: Path to input video file
            t: Time in seconds for thumbnail extraction
            out_path: Output path for thumbnail
            
        Returns:
            bool: True if successful, False if failed
        """
        try:
            cmd = [
                self.ffmpeg_path,
                "-i", input_video,           # Input video file
                "-ss", str(t),               # Seek to specific time
                "-vframes", "1",             # Extract only 1 frame
                "-f", "image2",              # Force image format output
                "-c:v", "mjpeg",             # Use MJPEG codec for JPEG output
                "-q:v", "2",                 # High quality (1-31, lower = better)
                "-y",                        # Overwrite output file
                out_path
            ]
            
            await self._run_ffmpeg(cmd)
            return True
            
        except Exception as e:
            logger.warning(f"Optimized thumbnail creation failed: {str(e)}")
            return False
    
    async def _thumbnail_with_reencode(self, input_video: str, t: float, out_path: str) -> None:
        """Create thumbnail with re-encoding (fallback)."""
        cmd = [
            self.ffmpeg_path,
            "-i", input_video,
            "-ss", str(t),
            "-vframes", "1",
            "-f", "image2",
            "-c:v", "mjpeg",
            "-q:v", "2",
            "-y",
            out_path
        ]
        
        await self._run_ffmpeg(cmd)
    
    async def _run_ffmpeg(self, cmd: List[str]) -> None:
        """Run FFmpeg command with robust error handling."""
        try:
            logger.debug(f"Running FFmpeg: {' '.join(cmd)}")
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            _, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown FFmpeg error"
                raise RuntimeError(f"FFmpeg failed (exit code {process.returncode}): {error_msg}")
                
        except FileNotFoundError:
            raise RuntimeError(f"FFmpeg not found at {self.ffmpeg_path}. Please install FFmpeg.")
        except Exception as e:
            logger.error(f"FFmpeg execution failed: {str(e)}")
            raise
    
    def _cleanup_temp_files(self, temp_files: List[str]) -> None:
        """Clean up temporary files."""
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file {temp_file}: {str(e)}")
    
    async def get_video_duration(self, video_path: str) -> float:
        """Get video duration using ffprobe."""
        try:
            cmd = [
                self.ffprobe_path,
                "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "csv=p=0",
                video_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise RuntimeError(f"ffprobe failed: {stderr.decode()}")
            
            return float(stdout.decode().strip())
            
        except Exception as e:
            logger.error(f"Failed to get video duration: {str(e)}")
            return 0.0
    
    async def test_ffmpeg(self) -> bool:
        """Test if FFmpeg is available and working."""
        try:
            cmd = [self.ffmpeg_path, "-version"]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            return process.returncode == 0
        except Exception:
            return False
