"""
Greedy segment selection and merging algorithm.
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class SegmentSelector:
    """Greedy algorithm for selecting and merging video segments."""
    
    def __init__(self, min_gap: float = 1.0, min_length: float = 2.0):
        """
        Initialize the segment selector.
        
        Args:
            min_gap: Maximum gap between segments to merge them (seconds)
            min_length: Minimum duration for a segment to be included (seconds)
        """
        self.min_gap = min_gap
        self.min_length = min_length
    
    def select(self, highlights_json: Dict[str, Any], target_seconds: int) -> List[Dict[str, Any]]:
        """
        Select segments using greedy algorithm with smart merging.
        
        Args:
            highlights_json: JSON with highlights array from ranker
            target_seconds: Target duration for final selection
            
        Returns:
            List of selected segments with start, end, label
        """
        try:
            highlights = highlights_json.get("highlights", [])
            
            if not highlights:
                logger.warning("No highlights provided")
                return []
            
            # Sort by score descending
            sorted_highlights = sorted(highlights, key=lambda x: x.get("score", 0), reverse=True)
            
            # Greedy selection while under target duration
            selected = self._greedy_selection(sorted_highlights, target_seconds)
            
            # Smart merge adjacent segments
            merged = self._smart_merge(selected)
            
            # Enforce minimum length and create final result
            final_segments = self._enforce_min_length(merged)
            
            logger.info(f"Selected {len(final_segments)} segments from {len(highlights)} highlights")
            return final_segments
            
        except Exception as e:
            logger.error(f"Segment selection failed: {str(e)}")
            return []
    
    def _greedy_selection(self, highlights: List[Dict], target_seconds: int) -> List[Dict]:
        """
        Greedy selection algorithm - add segments while under target duration.
        
        Args:
            highlights: Sorted highlights by score (descending)
            target_seconds: Target total duration
            
        Returns:
            List of selected segments
        """
        selected = []
        current_duration = 0.0
        target_with_buffer = target_seconds * 1.1  # Allow 10% buffer for better selection
        
        for highlight in highlights:
            start = highlight.get("start", 0)
            end = highlight.get("end", 0)
            duration = end - start
            
            # Skip segments that are too short
            if duration < self.min_length:
                continue
            
            # Check if adding this segment would exceed target
            if current_duration + duration > target_with_buffer:
                # Try to fit a truncated version if possible
                remaining_time = target_seconds - current_duration
                if remaining_time >= self.min_length:
                    # Truncate segment to fit
                    truncated_end = start + remaining_time
                    selected.append({
                        "start": start,
                        "end": truncated_end,
                        "label": highlight.get("label", ""),
                        "score": highlight.get("score", 0),
                        "reason": highlight.get("reason", "")
                    })
                break
            
            # Add full segment
            selected.append({
                "start": start,
                "end": end,
                "label": highlight.get("label", ""),
                "score": highlight.get("score", 0),
                "reason": highlight.get("reason", "")
            })
            current_duration += duration
        
        # If we're still under target, try to add more segments
        if current_duration < target_seconds * 0.8:  # If we're significantly under target
            for highlight in highlights[len(selected):]:
                start = highlight.get("start", 0)
                end = highlight.get("end", 0)
                duration = end - start
                
                if duration >= self.min_length and current_duration + duration <= target_seconds:
                    selected.append({
                        "start": start,
                        "end": end,
                        "label": highlight.get("label", ""),
                        "score": highlight.get("score", 0),
                        "reason": highlight.get("reason", "")
                    })
                    current_duration += duration
        
        return selected
    
    def _smart_merge(self, segments: List[Dict]) -> List[Dict]:
        """
        Smart merge adjacent segments with small gaps.
        
        Args:
            segments: List of selected segments
            
        Returns:
            List of merged segments
        """
        if not segments:
            return []
        
        # Sort by start time
        segments.sort(key=lambda x: x["start"])
        
        merged = []
        current_segment = segments[0].copy()
        
        for i in range(1, len(segments)):
            next_segment = segments[i]
            gap = next_segment["start"] - current_segment["end"]
            
            # Check if segments are close enough to merge
            if gap <= self.min_gap:
                # Merge segments
                current_segment["end"] = next_segment["end"]
                current_segment["label"] = f"{current_segment['label']} + {next_segment['label']}"
                current_segment["score"] = max(current_segment["score"], next_segment["score"])
                current_segment["reason"] = f"Merged: {current_segment['reason']} | {next_segment['reason']}"
            else:
                # Add current segment and start new one
                merged.append(current_segment)
                current_segment = next_segment.copy()
        
        # Add the last segment
        merged.append(current_segment)
        
        return merged
    
    def _enforce_min_length(self, segments: List[Dict]) -> List[Dict]:
        """
        Enforce minimum length requirement and create final result.
        
        Args:
            segments: List of segments to filter
            
        Returns:
            List of segments with start, end, label
        """
        final_segments = []
        
        for segment in segments:
            duration = segment["end"] - segment["start"]
            
            # Only include segments that meet minimum length
            if duration >= self.min_length:
                final_segments.append({
                    "start": segment["start"],
                    "end": segment["end"],
                    "label": segment["label"]
                })
            else:
                logger.debug(f"Dropped segment {segment['start']}-{segment['end']} (duration: {duration:.2f}s < {self.min_length}s)")
        
        return final_segments
    
    def calculate_total_duration(self, segments: List[Dict]) -> float:
        """Calculate total duration of selected segments."""
        return sum(seg["end"] - seg["start"] for seg in segments)
    
    def get_selection_stats(self, original_highlights: List[Dict], selected_segments: List[Dict]) -> Dict[str, Any]:
        """Get statistics about the selection process."""
        if not original_highlights or not selected_segments:
            return {}
        
        original_duration = sum(h.get("end", 0) - h.get("start", 0) for h in original_highlights)
        selected_duration = self.calculate_total_duration(selected_segments)
        
        return {
            "original_highlights": len(original_highlights),
            "selected_segments": len(selected_segments),
            "original_duration": original_duration,
            "selected_duration": selected_duration,
            "compression_ratio": selected_duration / original_duration if original_duration > 0 else 0,
            "average_segment_length": selected_duration / len(selected_segments) if selected_segments else 0
        }
