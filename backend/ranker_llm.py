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
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
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
            raise RuntimeError("LLM ranker not available - no API key or connection failed")
            
        try:
            # Test connection first
            if not await self.test_connection():
                raise RuntimeError("LLM service not accessible")
                
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
                content = response.choices[0].message.content
                if content is None:
                    raise ValueError("Empty response from LLM")
                highlights = self._parse_llm_response(content)
                
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
        
        return f"""You are a video summarization expert. Create the perfect {target_seconds}-second highlight reel from this transcript.

## 🎯 TASK
Select the BEST moments that tell the complete story in EXACTLY {target_seconds} seconds.

## 📋 SELECT THE BEST:
- Key insights and important information
- Conclusions and takeaways
- Actionable advice and practical tips
- Memorable quotes and emotional moments
- Data points and statistics
- Problem-solution pairs

## ⏱️ CRITICAL REQUIREMENTS:
- Total duration: EXACTLY {target_seconds} seconds (not more, not less)
- Maximum 6 segments (not 38!)
- Each segment: 8-15 seconds long
- Spread across timeline (beginning, middle, end)
- Quality over quantity - be VERY selective

## 🔍 QUALITY CHECKS
Before selecting each highlight, ask:
- Does this advance the main narrative?
- Is this information essential for understanding?
- Does this connect logically to other highlights?
- Would a viewer understand the context without additional segments?
- Is this segment temporally diverse from other selected highlights?

## 📍 TEMPORAL DISTRIBUTION STRATEGY
- **Beginning (0-25%)**: Include opening context, problem statement, or key introduction
- **Middle (25-75%)**: Cover main content, examples, explanations, and developments
- **End (75-100%)**: Include conclusions, takeaways, and final thoughts
- **Avoid clustering**: Don't select multiple segments from the same time period
- **Balance coverage**: Ensure all major topics/aspects are represented

## 📊 OUTPUT FORMAT
Return STRICT JSON only:
```json
{{
  "highlights": [
    {{
      "start": 45.2,
      "end": 52.8,
      "score": 0.9,
      "label": "Key insight about...",
      "reason": "Contains main conclusion with supporting data"
    }}
  ]
}}
```

## 🚫 AVOID
- Selecting segments that are too short (< 2 seconds) unless they contain critical information
- Creating highlights that don't connect to each other
- Including repetitive or redundant content
- Selecting segments with poor audio quality or unclear speech
- Choosing highlights that require extensive context to understand
- Artificially limiting segment length - let content determine appropriate duration

## 📝 SEGMENT ANALYSIS
For each potential highlight, consider:
- **Content Value**: How much essential information does it contain?
- **Narrative Position**: Where does it fit in the overall story?
- **Clarity**: Is the information clearly communicated?
- **Uniqueness**: Does it add something not covered elsewhere?

INPUT TRANSCRIPT SEGMENTS:
{segments_json}

Remember: You're creating a mini-documentary that tells the complete story in {target_seconds} seconds. Every second counts - make it compelling and informative."""
    
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
                
                # Enhanced duration validation (flexible for different video types)
                duration = end - start
                if duration < 2.0:
                    # Extend to minimum 2 seconds for better context
                    end = start + 2.0
                # Remove artificial upper limit - let the AI decide appropriate segment length
                
                # Validate against segment boundaries
                start, end = self._clamp_to_segments(start, end, segments)
                
                # Quality checks
                if self._is_quality_highlight(start, end, score, segments):
                    validated.append({
                        "start": start,
                        "end": end,
                        "score": max(0.0, min(1.0, score)),
                        "label": label,
                        "reason": reason
                    })
                else:
                    logger.debug(f"Highlight filtered out due to quality checks: {start}-{end}")
                    
            except (ValueError, KeyError) as e:
                logger.warning(f"Invalid highlight skipped: {e}")
                continue
        
        # Sort by score and apply final quality filters
        validated.sort(key=lambda x: x["score"], reverse=True)
        return self._apply_final_quality_filters(validated)
    
    def _is_quality_highlight(self, start: float, end: float, score: float, segments: List[Dict]) -> bool:
        """Check if highlight meets quality standards."""
        # Must have meaningful score
        if score < 0.3:
            return False
        
        # Must have reasonable duration (flexible for different content types)
        duration = end - start
        if duration < 1.0:  # Only filter out very short segments
            return False
        
        # Check if the segment contains meaningful content
        for seg in segments:
            if seg["start"] <= start <= seg["end"] and seg["start"] <= end <= seg["end"]:
                text = seg["text"].strip()
                # Filter out very short or repetitive content
                if len(text) < 20 or self._is_repetitive_content(text):
                    return False
                break
        
        return True
    
    def _is_repetitive_content(self, text: str) -> bool:
        """Check if text contains repetitive patterns."""
        words = text.lower().split()
        if len(words) < 5:
            return False
        
        # Check for repeated phrases
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        # If any word appears more than 30% of the time, it's repetitive
        max_frequency = max(word_counts.values()) / len(words)
        return max_frequency > 0.3
    
    def _apply_final_quality_filters(self, highlights: List[Dict]) -> List[Dict]:
        """Apply final quality filters to ensure coherent highlights."""
        if not highlights:
            return highlights
        
        # Remove overlapping highlights
        filtered = []
        for highlight in highlights:
            is_overlapping = False
            for existing in filtered:
                if self._highlights_overlap(highlight, existing):
                    # Keep the higher-scored highlight
                    if highlight["score"] > existing["score"]:
                        filtered.remove(existing)
                        break
                    else:
                        is_overlapping = True
                        break
            
            if not is_overlapping:
                filtered.append(highlight)
        
        # Ensure temporal coherence (highlights should flow logically)
        return self._ensure_temporal_coherence(filtered)
    
    def _highlights_overlap(self, h1: Dict, h2: Dict) -> bool:
        """Check if two highlights overlap in time."""
        return not (h1["end"] <= h2["start"] or h2["end"] <= h1["start"])
    
    def _ensure_temporal_coherence(self, highlights: List[Dict]) -> List[Dict]:
        """Ensure highlights are in temporal order and have good spacing."""
        # Sort by start time
        highlights.sort(key=lambda x: x["start"])
        
        # Remove highlights that are too close together (less than 5 seconds apart)
        filtered = []
        last_end = 0
        
        for highlight in highlights:
            if (highlight["start"] >= last_end + 5.0 or  # 5-second minimum gap
                highlight["score"] > 0.8):  # Keep high-scoring highlights even if close
                filtered.append(highlight)
                last_end = highlight["end"]
        
        return filtered
    
    def _clamp_to_segments(self, start: float, end: float, segments: List[Dict]) -> tuple:
        """Clamp highlight times to valid segment boundaries."""
        start_segment, end_segment = self._find_containing_segments(start, end, segments)
        
        # If we can't find containing segments, clamp to nearest
        if not start_segment:
            start_segment = self._find_nearest_start_segment(start, segments)
        if not end_segment:
            end_segment = self._find_nearest_end_segment(end, segments)
        
        # Clamp to segment boundaries
        if start_segment and end_segment:
            return self._clamp_to_boundaries(start, end, start_segment, end_segment)
        return start, end
    
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
