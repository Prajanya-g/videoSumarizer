"""
LLM-based ranking service for segment importance scoring.
"""

import json
import logging
import re
from typing import List, Dict, Any, Optional
import asyncio
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class LLMRanker:
    """LLM-based ranking service using OpenAI API."""
    
    def __init__(self, api_key: str = None, model: str = "gpt-3.5-turbo"):
        """
        Initialize the LLM ranker.
        
        Args:
            api_key: OpenAI API key (if None, will use environment variable)
            model: OpenAI model to use
        """
        try:
            self.client = AsyncOpenAI(api_key=api_key)
            self.model = model
            self.max_tokens_per_chunk = 3000  # ~2-3k tokens
            self.max_retries = 3
            self.available = True
        except Exception as e:
            logger.warning(f"LLM ranker initialization failed: {e}")
            self.available = False
    
    async def rank_segments(self, transcript_segments: List[Dict], target_seconds: int) -> Dict[str, Any]:
        """
        Rank transcription segments by importance using LLM.
        
        Args:
            transcript_segments: List of segment dicts with start, end, text
            target_seconds: Target duration for highlights
            
        Returns:
            Dict with highlights array
        """
        if not self.available:
            raise Exception("LLM ranker not available - no API key or connection failed")
            
        try:
            # Test connection first
            if not await self.test_connection():
                raise Exception("LLM service not accessible")
                
            # Chunk transcript into manageable pieces
            chunks = self._chunk_transcript(transcript_segments)
            
            all_highlights = []
            
            for i, chunk in enumerate(chunks):
                logger.info(f"Processing chunk {i+1}/{len(chunks)} with {len(chunk)} segments")
                
                # Get highlights for this chunk
                chunk_highlights = await self._rank_chunk(chunk, target_seconds)
                all_highlights.extend(chunk_highlights)
            
            # Sort all highlights by score and return
            all_highlights.sort(key=lambda x: x["score"], reverse=True)
            
            result = {
                "highlights": all_highlights
            }
            
            logger.info(f"LLM ranking completed: {len(all_highlights)} highlights selected")
            return result
            
        except Exception as e:
            logger.error(f"LLM ranking failed: {str(e)}")
            raise
    
    def _chunk_transcript(self, segments: List[Dict]) -> List[List[Dict]]:
        """Chunk transcript into ~2-3k token pieces."""
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for segment in segments:
            # Rough token estimation (4 chars per token)
            segment_tokens = len(segment["text"]) // 4
            
            if current_tokens + segment_tokens > self.max_tokens_per_chunk and current_chunk:
                chunks.append(current_chunk)
                current_chunk = [segment]
                current_tokens = segment_tokens
            else:
                current_chunk.append(segment)
                current_tokens += segment_tokens
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    async def _rank_chunk(self, chunk_segments: List[Dict], target_seconds: int) -> List[Dict]:
        """Rank a single chunk of segments."""
        for attempt in range(self.max_retries):
            try:
                # Create prompt
                prompt = self._create_ranking_prompt(chunk_segments, target_seconds)
                
                # Call LLM
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=2000
                )
                
                # Parse response
                highlights = self._parse_llm_response(response.choices[0].message.content)
                
                # Validate and cap highlights
                validated_highlights = self._validate_highlights(highlights, chunk_segments)
                
                return validated_highlights
                
            except Exception as e:
                logger.warning(f"LLM attempt {attempt + 1} failed: {str(e)}")
                if attempt == self.max_retries - 1:
                    # Final fallback: return empty highlights
                    return []
        
        return []
    
    def _create_ranking_prompt(self, segments: List[Dict], target_seconds: int) -> str:
        """Create the prompt for LLM ranking."""
        segments_json = json.dumps(segments, indent=2)
        
        return f"""You are selecting highlights from a video transcript with timestamps.
Goal: pick the most informative moments so a viewer gets the gist within {target_seconds}s.

Return STRICT JSON:
{{"highlights":[{{"start":float,"end":float,"score":0.0-1.0,"label":"short","reason":"short"}}]}}

Rules:
- Use transcript segment timestamps; don't invent times.
- Prefer moments that contain conclusions, definitions, numbers, or emotional peaks.
- Avoid filler and repetition.
- Each highlight 2–15s; prefer natural sentence boundaries.
- IMPORTANT: Aim for total duration close to {target_seconds}s. If you select too many highlights, prioritize the most important ones.
- Focus on key insights, main points, and memorable moments.
- Avoid redundant or repetitive content.

INPUT (segments):
{segments_json}"""
    
    def _parse_llm_response(self, response: str) -> List[Dict]:
        """Parse LLM response and extract highlights."""
        try:
            # Clean up response
            response = response.strip()
            
            # Try to find JSON in the response
            json_match = re.search(r'\{[^{}]*"highlights"[^{}]*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                # Try to find any JSON object
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end]
                else:
                    raise ValueError("No JSON found in response")
            
            # Parse JSON
            data = json.loads(json_str)
            
            if "highlights" not in data:
                raise ValueError("No highlights key in response")
            
            return data["highlights"]
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            raise ValueError(f"Invalid JSON: {str(e)}")
        except Exception as e:
            logger.error(f"Parse error: {str(e)}")
            raise ValueError(f"Failed to parse response: {str(e)}")
    
    def _validate_highlights(self, highlights: List[Dict], segments: List[Dict]) -> List[Dict]:
        """Validate and cap highlights to ensure they're within segment bounds."""
        validated = []
        
        # Create segment lookup for validation
        segment_lookup = {}
        for seg in segments:
            segment_lookup[(seg["start"], seg["end"])] = seg
        
        for highlight in highlights:
            try:
                start = float(highlight["start"])
                end = float(highlight["end"])
                score = float(highlight.get("score", 0.5))
                label = str(highlight.get("label", ""))
                reason = str(highlight.get("reason", ""))
                
                # Validate duration (2-15 seconds)
                duration = end - start
                if duration < 2.0:
                    # Extend to minimum 2 seconds
                    end = start + 2.0
                elif duration > 15.0:
                    # Cap to maximum 15 seconds
                    end = start + 15.0
                
                # Validate against segment boundaries
                start, end = self._clamp_to_segments(start, end, segments)
                
                # Only add if we have a valid range
                if end > start:
                    validated.append({
                        "start": start,
                        "end": end,
                        "score": max(0.0, min(1.0, score)),
                        "label": label,
                        "reason": reason
                    })
                    
            except (ValueError, KeyError) as e:
                logger.warning(f"Invalid highlight skipped: {e}")
                continue
        
        return validated
    
    def _clamp_to_segments(self, start: float, end: float, segments: List[Dict]) -> tuple:
        """Clamp highlight times to valid segment boundaries."""
        start_segment, end_segment = self._find_containing_segments(start, end, segments)
        
        # If we can't find containing segments, clamp to nearest
        if not start_segment:
            start_segment = self._find_nearest_start_segment(start, segments)
        if not end_segment:
            end_segment = self._find_nearest_end_segment(end, segments)
        
        # Clamp to segment boundaries
        return self._clamp_to_boundaries(start, end, start_segment, end_segment)
    
    def _find_containing_segments(self, start: float, end: float, segments: List[Dict]) -> tuple:
        """Find segments that contain the start and end times."""
        start_segment = None
        end_segment = None
        
        for seg in segments:
            if seg["start"] <= start <= seg["end"]:
                start_segment = seg
            if seg["start"] <= end <= seg["end"]:
                end_segment = seg
        
        return start_segment, end_segment
    
    def _find_nearest_start_segment(self, start: float, segments: List[Dict]) -> Optional[Dict]:
        """Find the nearest segment for the start time."""
        for seg in segments:
            if seg["start"] <= start:
                return seg
            else:
                break
        return None
    
    def _find_nearest_end_segment(self, end: float, segments: List[Dict]) -> Optional[Dict]:
        """Find the nearest segment for the end time."""
        for seg in reversed(segments):
            if seg["end"] >= end:
                return seg
            else:
                break
        return None
    
    def _clamp_to_boundaries(self, start: float, end: float, start_segment: Dict, end_segment: Dict) -> tuple:
        """Clamp times to segment boundaries."""
        if start_segment:
            start = max(start, start_segment["start"])
        if end_segment:
            end = min(end, end_segment["end"])
        
        return start, end
    
    async def test_connection(self) -> bool:
        """Test if the LLM service is accessible."""
        try:
            await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            return True
        except Exception as e:
            logger.error(f"LLM connection test failed: {str(e)}")
            return False
