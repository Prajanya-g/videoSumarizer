"""
GPT-powered video summarization pipeline.
"""

import asyncio
import json
import aiofiles
import time
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from backend.transcribe import TranscriptionService
from backend.ranker_llm import LLMRanker
from backend.render import VideoRenderer
from backend.services import JobService
from backend.schemas import JobStatus
from backend.logging_config import get_logger

logger = get_logger(__name__)

class VideoSummarizerPipeline:
    """GPT-powered pipeline for video summarization."""
    
    # Constants for file names
    JUMP_TO_FILE = "jump_to.json"
    THUMBNAIL_FILE = "thumb.jpg"
    
    def __init__(self, job_id: int, db_session):
        """
        Initialize the pipeline with job context and database session.
        
        Args:
            job_id: Database job ID
            db_session: SQLAlchemy database session
        """
        self.job_id = job_id
        self.db_session = db_session
        self.start_time = time.time()
        
        # Initialize AI services
        self.transcriber = TranscriptionService()
        self.llm_ranker = LLMRanker()
        self.renderer = VideoRenderer()
        
        # Processing metrics
        self.metrics = {
            "processing_time": 0,
            "token_count": 0,
            "cost_estimate": 0.0
        }
    
    async def run(self, target_seconds: int) -> None:
        """
        Run the complete AI-powered video summarization pipeline.
        
        Args:
            target_seconds: Target duration for highlights
        """
        try:
            # Update job status to processing
            self._update_job_status(JobStatus.PROCESSING)
            
            logger.info(f"Starting GPT-powered video processing pipeline for job: {self.job_id}")
            logger.info(f"Target duration: {target_seconds} seconds")
            
            job_dir = Path(f"data/jobs/{self.job_id}")
            job_dir.mkdir(parents=True, exist_ok=True)
            
            input_video = job_dir / "input.mp4"
            logger.info(f"Input video: {input_video}")
            
            # Step 1: Extract audio
            logger.info("Step 1/7: Extracting audio from video...")
            audio_path = await self._extract_audio(str(input_video))
            logger.info(f"Audio extracted successfully: {audio_path}")
            
            # Step 2: Transcribe with AI
            logger.info("Step 2/7: Transcribing audio with Whisper AI...")
            segments = await self._transcribe(audio_path)
            logger.info(f"AI transcription completed: {len(segments)} segments found")
            
            # Step 3: GPT-powered final selection
            logger.info("Step 3/6: GPT-powered final segment selection...")
            selected_segments = await self._gpt_select_segments(segments, target_seconds)
            logger.info(f"GPT selection completed: {len(selected_segments)} segments selected")
            
            # Step 4: Export highlights video
            logger.info("Step 4/6: Creating highlights video...")
            highlights_path = await self._export_highlights(str(input_video), selected_segments)
            logger.info(f"Highlights video created: {highlights_path}")
            
            # Step 5: Create jump_to.json and thumbnail
            logger.info("Step 5/6: Creating thumbnail and navigation data...")
            await self._create_jump_to_json(selected_segments, str(self.job_id))
            await self._create_thumbnail(highlights_path, str(self.job_id))
            logger.info("Thumbnail and navigation data created")
            
            # Step 6: Write result.json and update database
            logger.info("Step 6/6: Writing final results and updating database...")
            await self._write_result_json(str(self.job_id), selected_segments, target_seconds)
            self._update_job_paths(highlights_path, audio_path)
            self._update_job_status(JobStatus.COMPLETED)
            logger.info("Final results written and database updated")
            
            # Calculate and log metrics
            self._calculate_metrics()
            await self._log_processing_results()
            
            logger.info(f"GPT-powered pipeline completed successfully for job {self.job_id}")
            logger.info(f"Processing Metrics: {self.metrics}")
            logger.info(f"Results available at: http://localhost:8000/result/{self.job_id}")
            
        except Exception as e:
            logger.error(f"AI pipeline failed for job {self.job_id}: {str(e)}")
            self._update_job_status(JobStatus.FAILED, str(e))
            raise
    
    async def _extract_audio(self, input_video: str) -> str:
        """Extract audio from video file."""
        try:
            job_dir = Path(f"data/jobs/{self.job_id}")
            audio_path = job_dir / "audio.wav"
            
            logger.debug("Converting video to 16kHz mono audio...")
            
            cmd = [
                "ffmpeg",
                "-i", input_video,
                "-vn",  # No video
                "-acodec", "pcm_s16le",  # 16-bit PCM
                "-ar", "16000",  # 16kHz sample rate
                "-ac", "1",  # Mono
                "-y",  # Overwrite
                str(audio_path)
            ]
            
            await self._run_ffmpeg(cmd)
            logger.debug(f"Audio file ready: {audio_path}")
            return str(audio_path)
            
        except Exception as e:
            logger.error(f"Audio extraction failed: {str(e)}")
            logger.error(f"Audio extraction failed: {str(e)}")
            raise
    
    async def _transcribe(self, audio_path: str) -> list:
        """Transcribe audio and return segments."""
        try:
            logger.debug("Loading Whisper AI model (tiny) for fast processing...")
            segments = await self.transcriber.transcribe(audio_path, str(self.job_id))
            logger.debug(f"AI transcription completed: {len(segments)} segments")
            return segments
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            logger.error(f"Transcription failed: {str(e)}")
            raise
    
    async def _gpt_select_segments(self, segments: list, target_seconds: int) -> List[Dict[str, Any]]:
        """Let GPT do everything - select final segments directly."""
        try:
            logger.debug(f"Converting {len(segments)} segments for GPT analysis...")
            
            # Convert segments to dict format
            transcript_segments = [
                {"start": seg.start, "end": seg.end, "text": seg.text}
                for seg in segments
            ]
            
            # Let GPT do everything - no fallbacks, no complex algorithms
            logger.debug("Sending transcript to GPT-4 for complete segment selection...")
            start_time = time.time()
            highlights_json = await self.llm_ranker.rank_segments(transcript_segments, target_seconds)
            self.metrics["processing_time"] += time.time() - start_time
            
            # Extract final segments from GPT response
            selected_segments = highlights_json.get("highlights", [])
            
            # Validate and enforce duration limits
            selected_segments = self._validate_segments(selected_segments, target_seconds)
            
            logger.debug(f"GPT complete selection finished: {len(selected_segments)} segments")
            return selected_segments
                
        except Exception as e:
            logger.error(f"GPT selection failed: {str(e)}")
            raise
    
    def _validate_segments(self, segments: List[Dict], target_seconds: int) -> List[Dict]:
        """Validate and enforce duration limits on segments."""
        if not segments:
            return segments
        
        # Calculate total duration
        total_duration = sum(seg.get("end", 0) - seg.get("start", 0) for seg in segments)
        
        # If duration is way over target, take only the top segments
        if total_duration > target_seconds * 1.5:  # 50% over target
            logger.warning(f"GPT selected {len(segments)} segments with {total_duration:.1f}s duration (target: {target_seconds}s)")
            logger.warning("Taking only the top segments to meet duration requirements")
            
            # Sort by score and take top segments until we're close to target
            sorted_segments = sorted(segments, key=lambda x: x.get("score", 0), reverse=True)
            validated_segments = []
            current_duration = 0
            
            for segment in sorted_segments:
                segment_duration = segment.get("end", 0) - segment.get("start", 0)
                if current_duration + segment_duration <= target_seconds * 1.1:  # 10% buffer
                    validated_segments.append(segment)
                    current_duration += segment_duration
                else:
                    break
            
            logger.info(f"Reduced from {len(segments)} to {len(validated_segments)} segments")
            logger.info(f"Final duration: {current_duration:.1f}s (target: {target_seconds}s)")
            return validated_segments
        
        return segments
    
    async def _export_highlights(self, input_video: str, segments: list) -> str:
        """Export highlights video."""
        try:
            job_dir = Path(f"data/jobs/{self.job_id}")
            highlights_path = job_dir / "highlights.mp4"
            
            logger.debug(f"Concatenating {len(segments)} segments into highlights video...")
            await self.renderer.export_concat(input_video, segments, str(highlights_path))
            logger.debug(f"Highlights video created: {highlights_path}")
            return str(highlights_path)
            
        except Exception as e:
            logger.error(f"Highlights export failed: {str(e)}")
            logger.error(f"Highlights export failed: {str(e)}")
            raise
    
    async def _create_jump_to_json(self, segments: list, job_id: str) -> None:
        """Create jump_to.json for navigation."""
        try:
            job_dir = Path(f"data/jobs/{job_id}")
            jump_to_path = job_dir / self.JUMP_TO_FILE
            
            logger.debug(f"Creating navigation data for {len(segments)} highlights...")
            
            jump_to_data = {
                "highlights": [
                    {
                        "start": seg["start"],
                        "end": seg["end"],
                        "label": seg["label"]
                    }
                    for seg in segments
                ]
            }
            
            async with aiofiles.open(jump_to_path, "w") as f:
                await f.write(json.dumps(jump_to_data, indent=2))
            
            logger.debug(f"Navigation data created: {jump_to_path}")
            
        except Exception as e:
            logger.error(f"Navigation data creation failed: {str(e)}")
            logger.error(f"Jump-to JSON creation failed: {str(e)}")
            raise
    
    async def _create_thumbnail(self, highlights_path: str, job_id: str) -> None:
        """Create thumbnail from highlights video."""
        try:
            job_dir = Path(f"data/jobs/{job_id}")
            thumbnail_path = job_dir / self.THUMBNAIL_FILE
            
            logger.debug("Creating thumbnail from highlights video...")
            
            # Get video duration and use middle frame
            duration = await self.renderer.get_video_duration(highlights_path)
            thumbnail_time = duration / 2
            
            await self.renderer.make_thumbnail(highlights_path, thumbnail_time, str(thumbnail_path))
            logger.debug(f"Thumbnail created: {thumbnail_path}")
            
        except Exception as e:
            logger.error(f"Thumbnail creation failed: {str(e)}")
            logger.error(f"Thumbnail creation failed: {str(e)}")
            raise
    
    async def _write_result_json(self, job_id: str, segments: list, target_seconds: int) -> None:
        """Write final result.json with all metadata."""
        try:
            job_dir = Path(f"data/jobs/{job_id}")
            result_path = job_dir / "result.json"
            
            logger.debug("Calculating final statistics...")
            
            # Calculate statistics
            total_duration = sum(seg["end"] - seg["start"] for seg in segments)
            
            result_data = {
                "job_id": job_id,
                "status": "completed",
                "created_at": datetime.now().isoformat(),
                "target_seconds": target_seconds,
                "actual_duration": total_duration,
                "segments_count": len(segments),
                "files": {
                    "highlights_video": "highlights.mp4",
                    "thumbnail": self.THUMBNAIL_FILE,
                    "transcript": "transcript.json",
                    "transcript_srt": "transcript.srt",
                    "jump_to": self.JUMP_TO_FILE
                },
                "segments": segments
            }
            
            async with aiofiles.open(result_path, "w") as f:
                await f.write(json.dumps(result_data, indent=2))
            
            logger.debug(f"Final results written: {result_path}")
            logger.info(f"Summary: {len(segments)} segments, {total_duration:.1f}s total duration")
            
        except Exception as e:
            logger.error(f"Result JSON creation failed: {str(e)}")
            logger.error(f"Result JSON creation failed: {str(e)}")
            raise
    
    async def _run_ffmpeg(self, cmd: list) -> None:
        """Run FFmpeg command with error handling and timeout."""
        try:
            logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Add timeout to prevent hanging
            try:
                _, stderr = await asyncio.wait_for(process.communicate(), timeout=300)  # 5 minute timeout
            except asyncio.TimeoutError:
                process.kill()
                raise RuntimeError("FFmpeg command timed out after 5 minutes")
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown FFmpeg error"
                raise RuntimeError(f"FFmpeg failed: {error_msg}")
                
        except Exception as e:
            logger.error(f"FFmpeg execution failed: {str(e)}")
            raise
    
    def _update_job_status(self, status: JobStatus, error_message: str = None):
        """Update job status in database."""
        try:
            JobService.update_job_status(self.db_session, self.job_id, status, error_message)
            self.db_session.commit()
        except Exception as e:
            logger.error(f"Failed to update job status: {str(e)}")
            self.db_session.rollback()
    
    def _update_job_paths(self, highlights_path: str, audio_path: str):
        """Update job with output file paths."""
        try:
            job_dir = Path(f"data/jobs/{self.job_id}")
            
            # Update file paths in database
            JobService.update_job_file_paths(
                self.db_session,
                self.job_id,
                input_file_path=str(job_dir / "input.mp4"),
                audio_file_path=audio_path,
                transcript_file_path=str(job_dir / "transcript.json"),
                transcript_srt_path=str(job_dir / "transcript.srt"),
                highlights_file_path=highlights_path,
                thumbnail_file_path=str(job_dir / self.THUMBNAIL_FILE),
                jump_to_file_path=str(job_dir / self.JUMP_TO_FILE),
                result_file_path=str(job_dir / "result.json")
            )
            self.db_session.commit()
        except Exception as e:
            logger.error(f"Failed to update job paths: {str(e)}")
            self.db_session.rollback()
    
    def _calculate_metrics(self):
        """Calculate processing metrics."""
        self.metrics["processing_time"] = time.time() - self.start_time
        
        # GPT-4 metrics
        # Rough estimation: 1 token per 4 characters
        # GPT-4 pricing: ~$0.03 per 1K tokens
        estimated_tokens = 2000  # Conservative estimate
        self.metrics["token_count"] = estimated_tokens
        self.metrics["cost_estimate"] = (estimated_tokens / 1000) * 0.03
    
    async def _log_processing_results(self):
        """Log processing results."""
        logger.info("GPT Processing Results:")
        logger.info(f"Processing Time: {self.metrics['processing_time']:.2f}s")
        logger.info("AI Method: GPT-4 Complete Selection")
        logger.info(f"Estimated Cost: ${self.metrics['cost_estimate']:.4f}")
        logger.info("GPT handled everything - no fallbacks needed!")
        
        # Log to database for analytics
        try:
            # Store AI metrics in result.json
            result_path = Path(f"data/jobs/{self.job_id}/result.json")
            if result_path.exists():
                async with aiofiles.open(result_path, 'r') as f:
                    result_data = json.loads(await f.read())
                
                result_data["processing_metrics"] = self.metrics
                
                async with aiofiles.open(result_path, 'w') as f:
                    await f.write(json.dumps(result_data, indent=2))
        except Exception as e:
            logger.error(f"Failed to log processing results: {str(e)}")
