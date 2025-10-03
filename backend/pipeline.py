"""
Main pipeline orchestrator for video summarization.
"""

import asyncio
import json
import logging
import subprocess
import aiofiles
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from backend.transcribe import TranscriptionService
from backend.ranker_llm import LLMRanker
from backend.ranker_textrank import TextRankRanker
from backend.select_segments import SegmentSelector
from backend.render import VideoRenderer

logger = logging.getLogger(__name__)

class VideoSummarizerPipeline:
    """Main pipeline for video summarization."""
    
    def __init__(self):
        self.transcriber = TranscriptionService()
        self.llm_ranker = LLMRanker()
        self.textrank_ranker = TextRankRanker()
        self.segment_selector = SegmentSelector()
        self.renderer = VideoRenderer()
    
    async def run(self, job_id: str, target_seconds: int) -> None:
        """
        Run the complete video summarization pipeline.
        
        Args:
            job_id: Unique job identifier
            target_seconds: Target duration for highlights
        """
        try:
            print(f"\n🎬 Starting video processing pipeline for job: {job_id}")
            print(f"📊 Target duration: {target_seconds} seconds")
            
            job_dir = Path(f"data/jobs/{job_id}")
            job_dir.mkdir(parents=True, exist_ok=True)
            
            input_video = job_dir / "input.mp4"
            print(f"📁 Input video: {input_video}")
            
            # Step 1: Extract audio
            print("\n🎵 Step 1/7: Extracting audio from video...")
            audio_path = await self._extract_audio(str(input_video), job_id)
            print(f"✅ Audio extracted successfully: {audio_path}")
            
            # Step 2: Transcribe
            print("\n🎤 Step 2/7: Transcribing audio with Whisper...")
            segments = await self._transcribe(audio_path, job_id)
            print(f"✅ Transcription completed: {len(segments)} segments found")
            
            # Step 3: Rank segments
            print("\n🧠 Step 3/7: Ranking segments for importance...")
            highlights_json = await self._rank_segments(segments, target_seconds)
            print(f"✅ Ranking completed: {len(highlights_json.get('highlights', []))} highlights identified")
            
            # Step 4: Select segments
            print("\n✂️  Step 4/7: Selecting best segments for highlights...")
            selected_segments = self.segment_selector.select(highlights_json, target_seconds)
            print(f"✅ Segment selection completed: {len(selected_segments)} segments selected")
            
            # Step 5: Export highlights video
            print("\n🎞️  Step 5/7: Creating highlights video...")
            highlights_path = await self._export_highlights(str(input_video), selected_segments, job_id)
            print(f"✅ Highlights video created: {highlights_path}")
            
            # Step 6: Create jump_to.json and thumbnail
            print("\n🖼️  Step 6/7: Creating thumbnail and navigation data...")
            await self._create_jump_to_json(selected_segments, job_id)
            await self._create_thumbnail(highlights_path, job_id)
            print("✅ Thumbnail and navigation data created")
            
            # Step 7: Write result.json
            print("\n📄 Step 7/7: Writing final results...")
            await self._write_result_json(job_id, selected_segments, target_seconds)
            print("✅ Final results written")
            
            print(f"\n🎉 Pipeline completed successfully for job {job_id}")
            print(f"🔗 Results available at: http://localhost:8000/result/{job_id}")
            
        except Exception as e:
            print(f"\n❌ Pipeline failed for job {job_id}: {str(e)}")
            logger.error(f"Pipeline failed for job {job_id}: {str(e)}")
            raise
    
    async def _extract_audio(self, input_video: str, job_id: str) -> str:
        """Extract audio from video file."""
        try:
            job_dir = Path(f"data/jobs/{job_id}")
            audio_path = job_dir / "audio.wav"
            
            print("   🔧 Converting video to 16kHz mono audio...")
            
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
            print(f"   ✅ Audio file ready: {audio_path}")
            return str(audio_path)
            
        except Exception as e:
            print(f"   ❌ Audio extraction failed: {str(e)}")
            logger.error(f"Audio extraction failed: {str(e)}")
            raise
    
    async def _transcribe(self, audio_path: str, job_id: str) -> list:
        """Transcribe audio and return segments."""
        try:
            print("   🎧 Loading Whisper model (tiny) for fast processing...")
            segments = await self.transcriber.transcribe(audio_path, job_id)
            print(f"   ✅ Transcription completed: {len(segments)} segments")
            return segments
            
        except Exception as e:
            print(f"   ❌ Transcription failed: {str(e)}")
            logger.error(f"Transcription failed: {str(e)}")
            raise
    
    async def _rank_segments(self, segments: list, target_seconds: int) -> Dict[str, Any]:
        """Rank segments using LLM or TextRank fallback."""
        try:
            print(f"   📝 Converting {len(segments)} segments for analysis...")
            
            # Convert segments to dict format
            transcript_segments = [
                {"start": seg.start, "end": seg.end, "text": seg.text}
                for seg in segments
            ]
            
            # Try LLM ranking first
            try:
                print("   🤖 Sending transcript to GPT for intelligent ranking...")
                highlights_json = await self.llm_ranker.rank_segments(transcript_segments, target_seconds)
                print("   ✅ GPT ranking completed successfully")
                return highlights_json
                
            except Exception as e:
                print(f"   ⚠️  GPT ranking failed, using TextRank algorithm: {str(e)}")
                
                # Fallback to TextRank
                print("   📊 Using TextRank algorithm for ranking...")
                highlights_json = self.textrank_ranker.rank_segments(transcript_segments, target_seconds)
                print("   ✅ TextRank ranking completed")
                return highlights_json
                
        except Exception as e:
            print(f"   ❌ Ranking failed: {str(e)}")
            logger.error(f"Ranking failed: {str(e)}")
            raise
    
    async def _export_highlights(self, input_video: str, segments: list, job_id: str) -> str:
        """Export highlights video."""
        try:
            job_dir = Path(f"data/jobs/{job_id}")
            highlights_path = job_dir / "highlights.mp4"
            
            print(f"   🎬 Concatenating {len(segments)} segments into highlights video...")
            await self.renderer.export_concat(input_video, segments, str(highlights_path))
            print(f"   ✅ Highlights video created: {highlights_path}")
            return str(highlights_path)
            
        except Exception as e:
            print(f"   ❌ Highlights export failed: {str(e)}")
            logger.error(f"Highlights export failed: {str(e)}")
            raise
    
    async def _create_jump_to_json(self, segments: list, job_id: str) -> None:
        """Create jump_to.json for navigation."""
        try:
            job_dir = Path(f"data/jobs/{job_id}")
            jump_to_path = job_dir / "jump_to.json"
            
            print(f"   📋 Creating navigation data for {len(segments)} highlights...")
            
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
            
            print(f"   ✅ Navigation data created: {jump_to_path}")
            
        except Exception as e:
            print(f"   ❌ Navigation data creation failed: {str(e)}")
            logger.error(f"Jump-to JSON creation failed: {str(e)}")
            raise
    
    async def _create_thumbnail(self, highlights_path: str, job_id: str) -> None:
        """Create thumbnail from highlights video."""
        try:
            job_dir = Path(f"data/jobs/{job_id}")
            thumbnail_path = job_dir / "thumb.jpg"
            
            print("   🖼️  Creating thumbnail from highlights video...")
            
            # Get video duration and use middle frame
            duration = await self.renderer.get_video_duration(highlights_path)
            thumbnail_time = duration / 2
            
            await self.renderer.make_thumbnail(highlights_path, thumbnail_time, str(thumbnail_path))
            print(f"   ✅ Thumbnail created: {thumbnail_path}")
            
        except Exception as e:
            print(f"   ❌ Thumbnail creation failed: {str(e)}")
            logger.error(f"Thumbnail creation failed: {str(e)}")
            raise
    
    async def _write_result_json(self, job_id: str, segments: list, target_seconds: int) -> None:
        """Write final result.json with all metadata."""
        try:
            job_dir = Path(f"data/jobs/{job_id}")
            result_path = job_dir / "result.json"
            
            print("   📊 Calculating final statistics...")
            
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
                    "thumbnail": "thumb.jpg",
                    "transcript": "transcript.json",
                    "transcript_srt": "transcript.srt",
                    "jump_to": "jump_to.json"
                },
                "segments": segments
            }
            
            async with aiofiles.open(result_path, "w") as f:
                await f.write(json.dumps(result_data, indent=2))
            
            print(f"   ✅ Final results written: {result_path}")
            print(f"   📈 Summary: {len(segments)} segments, {total_duration:.1f}s total duration")
            
        except Exception as e:
            print(f"   ❌ Result JSON creation failed: {str(e)}")
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
