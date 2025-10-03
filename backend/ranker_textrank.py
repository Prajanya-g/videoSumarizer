"""
TextRank-based ranking service as a deterministic fallback.
"""

import logging
import re
from typing import List, Dict, Any
import numpy as np
from collections import defaultdict

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

logger = logging.getLogger(__name__)

class TextRankRanker:
    """TextRank-based ranking service for segment importance scoring."""
    
    def __init__(self, window_size: int = 2, damping_factor: float = 0.85):
        """
        Initialize the TextRank ranker.
        
        Args:
            window_size: Size of the sliding window for co-occurrence
            damping_factor: Damping factor for PageRank algorithm
        """
        self.window_size = window_size
        self.damping_factor = damping_factor
        self.nlp = None
        
        # Load spaCy model if available
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                logger.warning("spaCy model 'en_core_web_sm' not found. Install with: python -m spacy download en_core_web_sm")
                self.nlp = None
    
    def rank_segments(self, transcript_segments: List[Dict], target_seconds: int = None) -> Dict[str, Any]:  # pylint: disable=unused-argument
        """
        Rank transcription segments using TextRank algorithm.
        
        Args:
            transcript_segments: List of segment dicts with start, end, text
            target_seconds: Target duration for highlights (ignored in TextRank)
            
        Returns:
            Dict with highlights array in same format as LLM ranker
        """
        # Note: target_seconds parameter is ignored in TextRank algorithm
        _ = target_seconds  # Suppress unused parameter warning
        
        try:
            # Extract full text for sentence splitting
            full_text = " ".join([seg["text"] for seg in transcript_segments])
            
            # Split into sentences using spaCy
            sentences = self._split_sentences(full_text)
            
            if not sentences:
                logger.warning("No sentences found in transcript")
                return {"highlights": []}
            
            # Calculate TextRank scores for sentences
            sentence_scores = self._calculate_textrank_scores(sentences)
            
            # Map sentence scores back to segments
            segment_scores = self._map_sentence_scores_to_segments(
                transcript_segments, sentences, sentence_scores
            )
            
            # Create highlights in the same format as LLM ranker
            highlights = self._create_highlights(transcript_segments, segment_scores)
            
            logger.info(f"TextRank ranking completed: {len(highlights)} highlights selected")
            return {"highlights": highlights}
            
        except Exception as e:
            logger.error(f"TextRank ranking failed: {str(e)}")
            return {"highlights": []}
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences using spaCy or fallback method."""
        if self.nlp:
            # Use spaCy for better sentence splitting
            doc = self.nlp(text)
            sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
        else:
            # Fallback to simple regex splitting
            sentences = re.split(r'[.!?]+', text)
            sentences = [sent.strip() for sent in sentences if sent.strip()]
        
        return sentences
    
    def _calculate_textrank_scores(self, sentences: List[str]) -> List[float]:
        """Calculate TextRank scores for sentences."""
        if len(sentences) <= 1:
            return [1.0] * len(sentences)
        
        processed_sentences = [self._preprocess_text(sent) for sent in sentences]
        word_to_idx = self._build_vocabulary(processed_sentences)
        co_occurrence = self._build_cooccurrence_matrix(processed_sentences, word_to_idx)
        word_scores = self._pagerank(co_occurrence)
        sentence_scores = self._calculate_sentence_scores(processed_sentences, word_to_idx, word_scores)
        return self._normalize_scores(sentence_scores)
    
    def _build_vocabulary(self, processed_sentences: List[str]) -> Dict[str, int]:
        """Build vocabulary from processed sentences."""
        all_words = []
        for sent in processed_sentences:
            words = sent.split()
            all_words.extend(words)
        
        unique_words = list(set(all_words))
        return {word: i for i, word in enumerate(unique_words)}
    
    def _build_cooccurrence_matrix(self, processed_sentences: List[str], word_to_idx: Dict[str, int]) -> np.ndarray:
        """Build co-occurrence matrix from sentences."""
        n_words = len(word_to_idx)
        co_occurrence = np.zeros((n_words, n_words))
        
        for sent in processed_sentences:
            self._process_sentence_cooccurrence(sent, word_to_idx, co_occurrence)
        
        self._normalize_cooccurrence_matrix(co_occurrence)
        return co_occurrence
    
    def _process_sentence_cooccurrence(self, sentence: str, word_to_idx: Dict[str, int], co_occurrence: np.ndarray) -> None:
        """Process co-occurrence for a single sentence."""
        words = sentence.split()
        for i in range(len(words)):
            for j in range(max(0, i - self.window_size), 
                         min(len(words), i + self.window_size + 1)):
                if i != j:
                    word_i = words[i]
                    word_j = words[j]
                    if word_i in word_to_idx and word_j in word_to_idx:
                        idx_i = word_to_idx[word_i]
                        idx_j = word_to_idx[word_j]
                        co_occurrence[idx_i][idx_j] += 1
    
    def _normalize_cooccurrence_matrix(self, co_occurrence: np.ndarray) -> None:
        """Normalize co-occurrence matrix."""
        n_words = co_occurrence.shape[0]
        for i in range(n_words):
            row_sum = co_occurrence[i].sum()
            if row_sum > 0:
                co_occurrence[i] = co_occurrence[i] / row_sum
    
    def _calculate_sentence_scores(self, processed_sentences: List[str], word_to_idx: Dict[str, int], word_scores: np.ndarray) -> List[float]:
        """Calculate sentence scores based on word scores."""
        sentence_scores = []
        for sent in processed_sentences:
            words = sent.split()
            if not words:
                sentence_scores.append(0.0)
                continue
            
            sent_score = 0.0
            for word in words:
                if word in word_to_idx:
                    sent_score += word_scores[word_to_idx[word]]
            
            sentence_scores.append(sent_score / len(words))
        
        return sentence_scores
    
    def _normalize_scores(self, scores: List[float]) -> List[float]:
        """Normalize scores to [0, 1] range."""
        if not scores:
            return scores
        
        max_score = max(scores)
        min_score = min(scores)
        if max_score > min_score:
            return [(s - min_score) / (max_score - min_score) for s in scores]
        return scores
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for analysis."""
        # Convert to lowercase
        text = text.lower()
        # Remove punctuation
        text = re.sub(r'[^\w\s]', '', text)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _pagerank(self, matrix: np.ndarray, max_iter: int = 100, tol: float = 1e-6) -> np.ndarray:
        """Calculate PageRank scores for the given matrix."""
        n = matrix.shape[0]
        scores = np.ones(n) / n
        
        for _ in range(max_iter):
            prev_scores = scores.copy()
            scores = (1 - self.damping_factor) / n + self.damping_factor * matrix.T.dot(scores)
            
            if np.linalg.norm(scores - prev_scores) < tol:
                break
        
        return scores
    
    def _map_sentence_scores_to_segments(self, segments: List[Dict], sentences: List[str], sentence_scores: List[float]) -> List[float]:
        """Map sentence scores back to segment scores."""
        segment_scores = []
        
        for segment in segments:
            segment_text = segment["text"]
            max_sentence_score = 0.0
            
            # Find sentences that overlap with this segment
            for i, sentence in enumerate(sentences):
                # Simple overlap detection - check if segment text contains sentence or vice versa
                if (sentence.lower() in segment_text.lower() or 
                    segment_text.lower() in sentence.lower() or
                    self._text_overlap(sentence, segment_text)):
                    max_sentence_score = max(max_sentence_score, sentence_scores[i])
            
            # If no overlap found, use average score
            if abs(max_sentence_score) < 1e-9:
                max_sentence_score = np.mean(sentence_scores) if sentence_scores else 0.5
            
            segment_scores.append(max_sentence_score)
        
        return segment_scores
    
    def _text_overlap(self, text1: str, text2: str, threshold: float = 0.3) -> bool:
        """Check if two texts have significant overlap."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return False
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        overlap_ratio = len(intersection) / len(union)
        return overlap_ratio >= threshold
    
    def _create_highlights(self, segments: List[Dict], segment_scores: List[float]) -> List[Dict]:
        """Create highlights in the same format as LLM ranker."""
        highlights = []
        
        for i, (segment, score) in enumerate(zip(segments, segment_scores)):
            # Only include segments with meaningful scores
            if score > 0.1:  # Threshold for inclusion
                highlight = {
                    "start": segment["start"],
                    "end": segment["end"],
                    "score": float(score),
                    "label": f"TextRank highlight {i+1}",
                    "reason": f"TextRank score: {score:.3f}"
                }
                highlights.append(highlight)
        
        # Sort by score (descending)
        highlights.sort(key=lambda x: x["score"], reverse=True)
        
        return highlights
