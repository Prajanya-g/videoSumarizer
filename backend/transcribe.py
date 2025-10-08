"""
Whisper transcription service with chunking support for long files.
"""

import json
import logging
import os
import subprocess
import tempfile
import aiofiles
from pathlib import Path
from typing import List, Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor

try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    import whisper

logger = logging.getLogger(__name__)

def _create_temp_file(suffix: str) -> str:
    """Create a temporary file and return its path."""
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_file:
        return tmp_file.name

class Segment:
    """Simple segment class for transcription results."""
    def __init__(self, start: float, end: float, text: str):
        self.start = start
        self.end = end
        self.text = text
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "start": self.start,
            "end": self.end,
            "text": self.text
        }

class TranscriptionService:
    """Service for transcribing audio using Whisper with chunking support."""
    
    def __init__(self, model_size: str = "tiny", device: str = "auto"):
        """
        Initialize the transcription service.
        
        Args:
            model_size: Whisper model size ("tiny", "base", "small", "medium", "large")
            device: Device to use ("cpu", "cuda", "auto")
        """
        self.model_size = model_size
        self.device = device
        self.model = None
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.chunk_duration = 300  # 5 minutes per chunk
    
    async def transcribe(self, audio_path: str, job_id: str) -> List[Segment]:
        """
        Transcribe an audio file and save results to job folder.
        
        Args:
            audio_path: Path to the audio file
            job_id: Job ID for saving results
            
        Returns:
            List of Segment objects
        """
        try:
            # Convert to 16kHz WAV if needed
            wav_path = await self._ensure_16k_wav(audio_path)
            
            # Load model if not already loaded
            if self.model is None:
                await self._load_model()
            
            # Check if file needs chunking
            duration = await self._get_audio_duration(wav_path)
            logger.info(f"Audio duration: {duration:.2f} seconds")
            
            if duration > self.chunk_duration:
                segments = await self._transcribe_chunked(wav_path)
            else:
                segments = await self._transcribe_single(wav_path)
            
            # Save results to job folder
            await self._save_results(segments, job_id)
            
            logger.info(f"Transcription completed: {len(segments)} segments")
            return segments
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise
        finally:
            # Clean up temporary WAV file if it was created
            if 'wav_path' in locals() and wav_path != audio_path:
                try:
                    os.unlink(wav_path)
                except OSError:
                    pass
    
    async def _load_model(self):
        """Load the Whisper model with timeout."""
        loop = asyncio.get_event_loop()
        try:
            await asyncio.wait_for(
                loop.run_in_executor(self.executor, self._load_model_sync),
                timeout=120  # 2 minute timeout for model loading
            )
        except asyncio.TimeoutError:
            logger.error("Whisper model loading timed out")
            raise RuntimeError("Model loading timed out - try a smaller model")
    
    def _load_model_sync(self):
        """Synchronous model loading."""
        logger.info(f"Loading Whisper model: {self.model_size}")
        
        if FASTER_WHISPER_AVAILABLE:
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type="float16" if self.device == "cuda" else "int8"
            )
        else:
            self.model = whisper.load_model(self.model_size)
    
    async def _ensure_16k_wav(self, audio_path: str) -> str:
        """Convert audio to 16kHz WAV format."""
        # Check if already 16kHz WAV
        if audio_path.lower().endswith('.wav'):
            # Check sample rate
            try:
                process = await asyncio.create_subprocess_exec(
                    'ffprobe', '-v', 'quiet', '-show_entries', 'stream=sample_rate',
                    '-of', 'csv=p=0', audio_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                if process.returncode != 0:
                    raise subprocess.CalledProcessError(process.returncode, 'ffprobe')
                result = type('Result', (), {'stdout': stdout.decode()})()
                
                sample_rate = int(result.stdout.strip())
                if sample_rate == 16000:
                    return audio_path
            except (subprocess.CalledProcessError, ValueError):
                pass
        
        # Convert to 16kHz WAV
        wav_path = _create_temp_file('.wav')
        
        try:
            cmd = [
                'ffmpeg', '-i', audio_path,
                '-ar', '16000',  # 16kHz sample rate
                '-ac', '1',      # Mono
                '-y',            # Overwrite output
                wav_path
            ]
            
            process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, 'ffmpeg', stderr.decode())
            logger.info(f"Converted audio to 16kHz WAV: {wav_path}")
            return wav_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Audio conversion failed: {e.stderr}")
            raise
    
    async def _get_audio_duration(self, audio_path: str) -> float:
        """Get audio duration in seconds."""
        try:
            process = await asyncio.create_subprocess_exec(
                'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-of', 'csv=p=0', audio_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, 'ffprobe', stderr.decode())
            
            return float(stdout.decode().strip())
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get audio duration: {e.stderr}")
            return 0.0
    
    async def _transcribe_single(self, audio_path: str) -> List[Segment]:
        """Transcribe a single audio file with timeout."""
        loop = asyncio.get_event_loop()
        try:
            return await asyncio.wait_for(
                loop.run_in_executor(
                    self.executor,
                    self._transcribe_single_sync,
                    audio_path
                ),
                timeout=600  # 10 minute timeout for transcription
            )
        except asyncio.TimeoutError:
            logger.error("Transcription timed out")
            raise RuntimeError("Transcription timed out - audio file may be too long or corrupted")
    
    def _transcribe_single_sync(self, audio_path: str) -> List[Segment]:
        """Synchronous single file transcription."""
        try:
            if FASTER_WHISPER_AVAILABLE:
                # Use faster-whisper
                segments, _ = self.model.transcribe(
                    audio_path,
                    beam_size=5,
                    word_timestamps=True
                )
                
                result_segments = []
                for segment in segments:
                    result_segments.append(Segment(
                        start=segment.start,
                        end=segment.end,
                        text=segment.text.strip()
                    ))
                
                return result_segments
            else:
                # Use original whisper
                result = self.model.transcribe(
                    audio_path,
                    word_timestamps=True,
                    verbose=False
                )
                
                segments = []
                for segment in result["segments"]:
                    segments.append(Segment(
                        start=segment["start"],
                        end=segment["end"],
                        text=segment["text"].strip()
                    ))
                
                return segments
                
        except Exception as e:
            logger.error(f"Single transcription failed: {str(e)}")
            raise
    
    async def _transcribe_chunked(self, audio_path: str) -> List[Segment]:
        """Transcribe a long audio file by chunking."""
        duration = await self._get_audio_duration(audio_path)
        num_chunks = int(duration / self.chunk_duration) + 1
        
        logger.info(f"Audio duration: {duration:.1f}s - processing in {num_chunks} chunks of {self.chunk_duration}s each")
        
        all_segments = []
        
        for i in range(num_chunks):
            start_time = i * self.chunk_duration
            end_time = min((i + 1) * self.chunk_duration, duration)
            
            if start_time >= duration:
                break
            
            logger.debug(f"Processing chunk {i+1}/{num_chunks}: {start_time:.1f}s - {end_time:.1f}s")
            
            # Extract chunk
            chunk_path = await self._extract_chunk(audio_path, start_time, end_time)
            
            try:
                # Transcribe chunk
                chunk_segments = await self._transcribe_single(chunk_path)
                
                # Adjust timestamps to global time
                for segment in chunk_segments:
                    segment.start += start_time
                    segment.end += start_time
                
                all_segments.extend(chunk_segments)
                logger.debug(f"Chunk {i+1} completed: {len(chunk_segments)} segments")
                
            finally:
                # Clean up chunk file
                try:
                    os.unlink(chunk_path)
                except OSError:
                    pass
        
        # Sort segments by start time
        all_segments.sort(key=lambda x: x.start)
        
        return all_segments
    
    async def _extract_chunk(self, audio_path: str, start_time: float, end_time: float) -> str:
        """Extract a time chunk from audio file."""
        chunk_path = _create_temp_file('.wav')
        
        try:
            cmd = [
                'ffmpeg', '-i', audio_path,
                '-ss', str(start_time),
                '-t', str(end_time - start_time),
                '-ar', '16000',
                '-ac', '1',
                '-y',
                chunk_path
            ]
            
            process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            _, stderr = await process.communicate()
            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, 'ffmpeg', stderr.decode())
            return chunk_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Chunk extraction failed: {e.stderr}")
            raise
    
    async def _save_results(self, segments: List[Segment], job_id: str):
        """Save transcription results to job folder."""
        job_dir = Path(f"data/jobs/{job_id}")
        job_dir.mkdir(parents=True, exist_ok=True)
        
        # Save transcript.json
        transcript_data = {
            "segments": [seg.to_dict() for seg in segments],
            "full_text": " ".join([seg.text for seg in segments]),
            "total_duration": max([seg.end for seg in segments]) if segments else 0.0
        }
        
        async with aiofiles.open(job_dir / "transcript.json", "w") as f:
            await f.write(json.dumps(transcript_data, indent=2))
        
        # Save transcript.srt
        await self._save_srt(segments, job_dir / "transcript.srt")
        
        logger.info(f"Saved transcription results to {job_dir}")
    
    async def _save_srt(self, segments: List[Segment], srt_path: Path):
        """Save segments as SRT subtitle file."""
        async with aiofiles.open(srt_path, "w", encoding="utf-8") as f:
            for i, segment in enumerate(segments, 1):
                start_time = self._format_srt_time(segment.start)
                end_time = self._format_srt_time(segment.end)
                
                await f.write(f"{i}\n")
                await f.write(f"{start_time} --> {end_time}\n")
                await f.write(f"{segment.text}\n\n")
    
    def _format_srt_time(self, seconds: float) -> str:
        """Format seconds to SRT time format (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def cleanup(self):
        """Clean up resources."""
        if self.executor:
            self.executor.shutdown(wait=True)
