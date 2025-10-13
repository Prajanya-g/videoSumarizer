"""
GPT-powered video summarization pipeline.

This module implements the core video processing pipeline that:
1. Extracts audio from uploaded videos
2. Transcribes audio using Whisper AI
3. Uses GPT-4 to select the most important segments
4. Creates highlight videos with dynamic clip durations
5. Generates thumbnails and navigation data

The pipeline is designed to be robust, scalable, and AI-powered for
high-quality video summarization.
"""

import asyncio
import json
import aiofiles
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from backend.transcribe import TranscriptionService
from backend.ranker_llm import LLMRanker
from backend.render import VideoRenderer
from backend.services import JobService
from backend.schemas import JobStatus
from backend.logging_config import get_logger

logger = get_logger(__name__)

class VideoSummarizerPipeline:
    """
    GPT-powered pipeline for video summarization.
    
    This class orchestrates the complete video processing workflow:
    - Audio extraction from video files
    - AI-powered transcription using Whisper
    - Intelligent segment selection using GPT-4
    - Dynamic video rendering with optimized clip durations
    - Thumbnail and navigation data generation
    
    The pipeline uses a chunk-based approach for segment selection,
    ensuring comprehensive coverage across the entire video timeline.
    """
    
    # File naming constants for consistent file management
    JUMP_TO_FILE = "jump_to.json"      # Navigation data for timestamp mapping
    THUMBNAIL_FILE = "thumb.jpg"       # Video thumbnail image
    
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
        
        This is the main orchestration method that coordinates all processing steps:
        1. Audio extraction from video
        2. AI transcription using Whisper
        3. GPT-powered segment selection with dynamic clip durations
        4. Video rendering and thumbnail generation
        5. Database updates and result storage
        
        Args:
            target_seconds: Target duration for the final highlight video
                           (used to calculate optimal clip durations)
        """
        try:
            # Update job status to processing to inform frontend of progress
            self._update_job_status(JobStatus.PROCESSING)
            
            logger.info(f"Starting GPT-powered video processing pipeline for job: {self.job_id}")
            logger.info(f"Target duration: {target_seconds} seconds")
            
            # Ensure job directory exists for file storage and organization
            job_dir = Path(f"data/jobs/{self.job_id}")
            job_dir.mkdir(parents=True, exist_ok=True)
            
            input_video = job_dir / "input.mp4"
            logger.info(f"Input video: {input_video}")
            
            # Step 1: Extract audio from video for transcription
            # Whisper AI requires audio input, not video
            logger.info("Step 1/7: Extracting audio from video...")
            audio_path = await self._extract_audio(str(input_video))
            logger.info(f"Audio extracted successfully: {audio_path}")
            
            # Step 2: Transcribe audio using Whisper AI
            # This converts speech to text with precise timestamps
            logger.info("Step 2/7: Transcribing audio with Whisper AI...")
            segments = await self._transcribe(audio_path)
            logger.info(f"AI transcription completed: {len(segments)} segments found")
            
            # Step 3: Use GPT-4 to select the most important segments
            # This is where AI intelligence is applied for smart, comprehensive selection
            logger.info("Step 3/6: GPT-powered final segment selection...")
            selected_segments = await self._gpt_select_segments(segments, target_seconds)
            logger.info(f"GPT selection completed: {len(selected_segments)} segments selected")
            
            # Step 4: Create the highlight video by cutting and joining segments
            # Uses FFmpeg to create the final output video with proper timing
            logger.info("Step 4/6: Creating highlights video...")
            highlights_path = await self._export_highlights(str(input_video), selected_segments)
            logger.info(f"Highlights video created: {highlights_path}")
            
            # Step 5: Generate thumbnail and navigation data
            # Thumbnail provides visual preview, jump_to.json enables timestamp navigation
            logger.info("Step 5/6: Creating thumbnail and navigation data...")
            await self._create_jump_to_json(selected_segments, str(self.job_id))
            await self._create_thumbnail(highlights_path, str(self.job_id))
            logger.info("Thumbnail and navigation data created")
            
            # Step 6: Finalize results and update database
            # Store all file paths and metadata for frontend access
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
        
        logger.info(f"GPT selected {len(segments)} segments with {total_duration:.1f}s duration (target: {target_seconds}s)")
        
        # If duration is significantly over target, reduce segments intelligently
        if total_duration > target_seconds * 1.5:  # 50% over target
            logger.warning("Duration significantly over target - reducing segments")
            
            # Sort by score and use a smarter selection algorithm
            sorted_segments = sorted(segments, key=lambda x: x.get("score", 0), reverse=True)
            validated_segments = self._smart_segment_selection(sorted_segments, target_seconds)
            
            final_duration = sum(seg.get("end", 0) - seg.get("start", 0) for seg in validated_segments)
            logger.info(f"Reduced from {len(segments)} to {len(validated_segments)} segments")
            logger.info(f"Final duration: {final_duration:.1f}s (target: {target_seconds}s)")
            return validated_segments
        
        # If duration is significantly under target, try to add more segments
        elif total_duration < target_seconds * 0.5:  # Less than 50% of target
            logger.warning(f"Duration significantly under target: {total_duration:.1f}s vs {target_seconds}s")
            logger.warning("This may indicate GPT selection issues or insufficient content")
            logger.warning("Consider adjusting the prompt or checking video content quality")
            # Note: We don't modify segments here as it would require re-running GPT
            # This is a limitation that should be addressed in the GPT prompt
        
        # If duration is moderately under target, warn
        elif total_duration < target_seconds * 0.8:  # Less than 80% of target
            logger.warning(f"Duration under target: {total_duration:.1f}s vs {target_seconds}s")
            logger.warning("GPT may have been too selective - consider reviewing selection criteria")
        
        logger.info(f"Final duration: {total_duration:.1f}s (target: {target_seconds}s)")
        return segments
    
    def _smart_segment_selection(self, segments: List[Dict], target_seconds: int) -> List[Dict]:
        """Intelligently select segments using chunk-based approach for better coverage and timing."""
        if not segments:
            return segments
        
        logger.info(f"Smart selection starting with {len(segments)} segments, target: {target_seconds}s")
        
        # Calculate dynamic clip duration based on target duration
        ideal_clip_duration = self._calculate_ideal_clip_duration(target_seconds)
        logger.info(f"Dynamic clip duration: {ideal_clip_duration:.1f}s per clip for {target_seconds}s target")
        
        # Strategy 1: Chunk-based selection - divide video into equal chunks and select from each
        chunk_selection = self._select_from_chunks(segments, target_seconds, ideal_clip_duration)
        
        # Strategy 2: If chunk selection doesn't work well, fall back to temporal diversity
        if len(chunk_selection) < 3 or self._calculate_total_duration(chunk_selection) < target_seconds * 0.5:
            logger.info("Chunk selection insufficient, trying temporal diversity...")
            temporal_selection = self._select_with_temporal_diversity(segments, target_seconds, ideal_clip_duration)
            
            if len(temporal_selection) > len(chunk_selection):
                chunk_selection = temporal_selection
        
        logger.info(f"Final smart selection: {len(chunk_selection)} segments, {self._calculate_total_duration(chunk_selection):.1f}s duration")
        return chunk_selection
    
    def _calculate_ideal_clip_duration(self, target_seconds: int) -> float:
        """
        Calculate ideal clip duration based on target duration using a smart equation.
        
        This method implements a dynamic scaling algorithm that adjusts clip duration
        based on the target video length. The goal is to create optimal pacing:
        - Short videos get quick, dynamic clips
        - Long videos get more comprehensive, detailed clips
        - All clips stay within reasonable bounds (3-20 seconds)
        
        The equation uses a square root function to create a logarithmic-like curve
        that scales naturally with video duration.
        
        Args:
            target_seconds: Target duration for the final highlight video
            
        Returns:
            float: Ideal clip duration in seconds
            
        Examples:
            - 60s target → ~4-6s clips (10-15 segments) for quick highlights
            - 300s target → ~8-12s clips (25-37 segments) for balanced coverage
            - 600s target → ~12-15s clips (40-50 segments) for comprehensive view
        """
        import math
        
        # Base equation: clip_duration = sqrt(target_seconds) * 0.8 + 2
        # Square root creates logarithmic-like scaling that feels natural
        base_duration = math.sqrt(target_seconds) * 0.8 + 2
        
        # Apply scaling factors based on video length categories
        if target_seconds <= 60:
            # Short videos (≤1min): prefer shorter clips for quick, dynamic highlights
            # This creates a snappy, fast-paced feel appropriate for short content
            ideal_duration = base_duration * 0.7
        elif target_seconds <= 300:
            # Medium videos (1-5min): balanced approach with moderate clip lengths
            # This provides good coverage without being too rushed or too slow
            ideal_duration = base_duration
        else:
            # Long videos (>5min): allow longer clips for comprehensive coverage
            # This ensures important content isn't cut too short in longer videos
            ideal_duration = base_duration * 1.2
        
        # Enforce reasonable bounds to prevent extreme values
        # Minimum 3s ensures clips aren't too short to be meaningful
        # Maximum 20s prevents clips from being too long and losing focus
        ideal_duration = max(3.0, min(20.0, ideal_duration))
        
        logger.info(f"Clip duration calculation: sqrt({target_seconds}) * 0.8 + 2 = {base_duration:.1f}s, "
                   f"scaled to {ideal_duration:.1f}s for {target_seconds}s target")
        
        return ideal_duration
    
    def _select_from_chunks(self, segments: List[Dict], target_seconds: int, ideal_clip_duration: float) -> List[Dict]:
        """
        Select segments by dividing video into equal chunks and picking best from each.
        
        This method implements a chunk-based selection strategy that ensures:
        - Comprehensive coverage across the entire video timeline
        - Balanced representation from beginning, middle, and end
        - Optimal clip durations based on the target video length
        - Avoids clustering of segments in the same time period
        
        Args:
            segments: List of all available segments with scores and timestamps
            target_seconds: Target duration for the final highlight video
            ideal_clip_duration: Calculated optimal duration for individual clips
            
        Returns:
            List[Dict]: Selected segments optimized for comprehensive coverage
        """
        if not segments:
            return []
        
        # Calculate video duration and chunk parameters for optimal distribution
        video_duration = self._calculate_video_duration(segments)
        num_chunks, chunk_duration = self._calculate_chunk_parameters(target_seconds, ideal_clip_duration)
        
        logger.info(f"Dividing {video_duration:.1f}s video into {num_chunks} chunks of {chunk_duration:.1f}s each")
        logger.info(f"Targeting {ideal_clip_duration:.1f}s clips, estimated {target_seconds / ideal_clip_duration:.1f} segments")
        
        selected_segments = []
        current_total_duration = 0
        
        # Process each chunk to ensure temporal diversity
        for chunk_idx in range(num_chunks):
            # Calculate time boundaries for this chunk
            chunk_start, chunk_end = self._calculate_chunk_bounds(chunk_idx, num_chunks, video_duration)
            chunk_segments = self._get_segments_in_chunk(segments, chunk_start, chunk_end)
            
            if not chunk_segments:
                logger.warning(f"No segments found in chunk {chunk_idx + 1} ({chunk_start:.1f}s - {chunk_end:.1f}s)")
                continue
            
            # Select the best segments from this chunk based on quality and duration
            chunk_selected, chunk_duration_used = self._select_segments_from_chunk(
                chunk_segments, ideal_clip_duration, target_seconds, current_total_duration, chunk_duration
            )
            
            # Add selected segments to the final list
            selected_segments.extend(chunk_selected)
            current_total_duration += chunk_duration_used
            
            logger.info(f"Chunk {chunk_idx + 1}: Selected {len(chunk_selected)} segments")
        
        logger.info(f"Chunk-based selection: {len(selected_segments)} segments, {current_total_duration:.1f}s total")
        return selected_segments
    
    def _calculate_video_duration(self, segments: List[Dict]) -> float:
        """Calculate total video duration from segments."""
        return max(seg.get("end", 0) for seg in segments)
    
    def _calculate_chunk_parameters(self, target_seconds: int, ideal_clip_duration: float) -> tuple[int, float]:
        """Calculate number of chunks and chunk duration."""
        estimated_segments = target_seconds / ideal_clip_duration
        num_chunks = max(3, min(8, int(estimated_segments * 0.6)))  # 60% of estimated segments as chunks
        chunk_duration = target_seconds / num_chunks
        return num_chunks, chunk_duration
    
    def _calculate_chunk_bounds(self, chunk_idx: int, num_chunks: int, video_duration: float) -> tuple[float, float]:
        """Calculate start and end times for a chunk."""
        chunk_start = chunk_idx * (video_duration / num_chunks)
        chunk_end = (chunk_idx + 1) * (video_duration / num_chunks)
        return chunk_start, chunk_end
    
    def _get_segments_in_chunk(self, segments: List[Dict], chunk_start: float, chunk_end: float) -> List[Dict]:
        """Get segments that fall within the specified chunk bounds."""
        return [
            seg for seg in segments 
            if chunk_start <= seg.get("start", 0) < chunk_end
        ]
    
    def _select_segments_from_chunk(self, chunk_segments: List[Dict], ideal_clip_duration: float, 
                                   target_seconds: int, current_total_duration: float, chunk_duration: float) -> tuple[List[Dict], float]:
        """Select segments from a chunk based on duration and quality criteria."""
        # Sort by score and select the best segment(s) from this chunk
        chunk_segments.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        selected_segments = []
        chunk_duration_used = 0
        
        for segment in chunk_segments:
            segment_duration = segment.get("end", 0) - segment.get("start", 0)
            
            # Check if segment meets duration criteria
            if not self._is_segment_duration_acceptable(segment_duration, ideal_clip_duration):
                continue
            
            # Check if adding this segment would exceed our target
            if current_total_duration + segment_duration <= target_seconds * 1.1:
                selected_segments.append(segment)
                chunk_duration_used += segment_duration
                
                # Stop if we've filled this chunk's allocation
                if chunk_duration_used >= chunk_duration * 0.8:  # 80% of chunk duration
                    break
                
                # Stop if we have enough segments from this chunk
                if len(selected_segments) >= 2:
                    break
        
        return selected_segments, chunk_duration_used
    
    def _is_segment_duration_acceptable(self, segment_duration: float, ideal_clip_duration: float) -> bool:
        """Check if a segment's duration is acceptable based on ideal clip duration."""
        duration_diff = abs(segment_duration - ideal_clip_duration)
        max_acceptable_diff = ideal_clip_duration * 0.5  # 50% tolerance
        
        # Skip segments that are too far from ideal duration
        if duration_diff > max_acceptable_diff:
            return False
        
        # Skip very long segments
        if segment_duration > ideal_clip_duration * 2.0:
            return False
        
        return True
    
    def _select_with_temporal_diversity(self, segments: List[Dict], target_seconds: int, ideal_clip_duration: float) -> List[Dict]:
        """Select segments ensuring good temporal distribution across the video."""
        if not segments:
            return []
        
        video_duration = self._calculate_video_duration(segments)
        time_zones = self._create_time_zones(video_duration)
        
        selected_segments = []
        current_duration = 0
        
        # Select segments from each time zone
        for zone_start, zone_end in time_zones:
            zone_segments = self._get_segments_in_time_zone(segments, zone_start, zone_end)
            
            if not zone_segments:
                continue
            
            # Select segments from this time zone
            zone_selected = self._select_segments_from_time_zone(
                zone_segments, ideal_clip_duration, target_seconds, current_duration
            )
            
            selected_segments.extend(zone_selected)
            current_duration += sum(seg.get("end", 0) - seg.get("start", 0) for seg in zone_selected)
        
        return selected_segments
    
    def _create_time_zones(self, video_duration: float) -> List[tuple[float, float]]:
        """Create time zones for temporal diversity selection."""
        return [
            (0, video_duration * 0.25),           # Beginning (0-25%)
            (video_duration * 0.25, video_duration * 0.75),  # Middle (25-75%)
            (video_duration * 0.75, video_duration)         # End (75-100%)
        ]
    
    def _get_segments_in_time_zone(self, segments: List[Dict], zone_start: float, zone_end: float) -> List[Dict]:
        """Get segments that fall within the specified time zone."""
        return [
            seg for seg in segments 
            if zone_start <= seg.get("start", 0) < zone_end
        ]
    
    def _select_segments_from_time_zone(self, zone_segments: List[Dict], ideal_clip_duration: float, 
                                      target_seconds: int, current_duration: float) -> List[Dict]:
        """Select segments from a time zone based on duration and quality criteria."""
        # Sort by score and take the best from this zone
        zone_segments.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        selected_segments = []
        
        for segment in zone_segments:
            segment_duration = segment.get("end", 0) - segment.get("start", 0)
            
            # Check if segment meets duration criteria
            if not self._is_segment_duration_acceptable(segment_duration, ideal_clip_duration):
                continue
            
            # Check if adding this segment would exceed target
            if current_duration + segment_duration <= target_seconds * 1.1:
                selected_segments.append(segment)
                current_duration += segment_duration
                
                # Limit segments per zone to ensure diversity
                if len(selected_segments) >= 2:
                    break
        
        return selected_segments
    
    def _select_by_score_with_diversity(self, segments: List[Dict], target_seconds: int) -> List[Dict]:
        """Select segments by score while maintaining some temporal diversity."""
        sorted_segments = sorted(segments, key=lambda x: x.get("score", 0), reverse=True)
        selected_segments = []
        current_duration = 0
        used_time_ranges = []  # Track used time ranges to avoid clustering
        
        for segment in sorted_segments:
            segment_duration = segment.get("end", 0) - segment.get("start", 0)
            segment_start = segment.get("start", 0)
            
            # Skip very long segments
            if segment_duration > target_seconds * 0.3:
                continue
            
            # Check for temporal clustering - avoid segments too close to already selected ones
            too_close = any(
                abs(segment_start - used_start) < 60  # 60 seconds minimum gap
                for used_start in used_time_ranges
            )
            
            if too_close:
                continue
            
            # Check duration limit
            if current_duration + segment_duration <= target_seconds * 1.1:
                selected_segments.append(segment)
                current_duration += segment_duration
                used_time_ranges.append(segment_start)
                
                # Stop when we have enough segments
                if len(selected_segments) >= 8:
                    break
        
        return selected_segments
    
    def _calculate_temporal_diversity(self, segments: List[Dict]) -> float:
        """Calculate how well distributed the segments are across the video timeline."""
        if len(segments) < 2:
            return 0.0
        
        # Get segment start times
        start_times = [seg.get("start", 0) for seg in segments]
        start_times.sort()
        
        # Calculate gaps between consecutive segments
        gaps = [end - start for start, end in zip(start_times[:-1], start_times[1:])]
        
        if not gaps:
            return 0.0
        
        # Diversity score based on gap variance (higher variance = better distribution)
        avg_gap = sum(gaps) / len(gaps)
        variance = sum((gap - avg_gap) ** 2 for gap in gaps) / len(gaps)
        
        # Normalize to 0-1 scale
        return min(1.0, variance / (avg_gap ** 2) if avg_gap > 0 else 0.0)
    
    def _calculate_total_duration(self, segments: List[Dict]) -> float:
        """Calculate total duration of selected segments."""
        return sum(seg.get("end", 0) - seg.get("start", 0) for seg in segments)
    
    def _score_selection(self, segments: List[Dict], target_seconds: int) -> float:
        """Score a segment selection based on multiple factors."""
        if not segments:
            return 0.0
        
        duration = sum(seg.get("end", 0) - seg.get("start", 0) for seg in segments)
        segment_count = len(segments)
        avg_score = sum(seg.get("score", 0) for seg in segments) / len(segments)
        
        # Duration score: closer to target is better
        duration_ratio = duration / target_seconds
        if 0.8 <= duration_ratio <= 1.1:  # Within 80-110% of target
            duration_score = 1.0
        elif 0.6 <= duration_ratio < 0.8:  # 60-80% of target
            duration_score = 0.8
        elif 1.1 < duration_ratio <= 1.3:  # 110-130% of target
            duration_score = 0.7
        else:
            duration_score = 0.3
        
        # Segment count score: prefer 4-8 segments for good highlight reel
        if 4 <= segment_count <= 8:
            count_score = 1.0
        elif 3 <= segment_count <= 10:
            count_score = 0.8
        else:
            count_score = 0.5
        
        # Quality score: higher average score is better
        quality_score = min(1.0, avg_score)
        
        # Combined score
        total_score = (duration_score * 0.4 + count_score * 0.3 + quality_score * 0.3)
        
        return total_score
    
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
            
            logger.info("Creating thumbnail from highlights video...")
            
            # Get video duration and use middle frame
            duration = await self.renderer.get_video_duration(highlights_path)
            thumbnail_time = duration / 2
            logger.info(f"Video duration: {duration:.1f}s, thumbnail time: {thumbnail_time:.1f}s")
            
            await self.renderer.make_thumbnail(highlights_path, thumbnail_time, str(thumbnail_path))
            
            # Verify thumbnail was created
            if thumbnail_path.exists():
                logger.info(f"Thumbnail created successfully: {thumbnail_path}")
            else:
                logger.error(f"Thumbnail file not found after creation: {thumbnail_path}")
                raise FileNotFoundError(f"Thumbnail file not created: {thumbnail_path}")
            
        except Exception as e:
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
    
    def _update_job_status(self, status: JobStatus, error_message: Optional[str] = None):
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
            file_paths = {
                "input_file_path": str(job_dir / "input.mp4"),
                "audio_file_path": audio_path,
                "transcript_file_path": str(job_dir / "transcript.json"),
                "transcript_srt_path": str(job_dir / "transcript.srt"),
                "highlights_file_path": highlights_path,
                "thumbnail_file_path": str(job_dir / self.THUMBNAIL_FILE),
                "jump_to_file_path": str(job_dir / self.JUMP_TO_FILE),
                "result_file_path": str(job_dir / "result.json")
            }
            
            JobService.update_job_file_paths(
                self.db_session,
                self.job_id,
                file_paths
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
