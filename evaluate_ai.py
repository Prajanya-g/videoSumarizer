#!/usr/bin/env python3
"""
AI Feature Evaluation Script for Video Summarizer.

This script evaluates the AI-powered video summarization feature
by testing it on sample video content and measuring performance.
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from backend.ranker_llm import LLMRanker
from backend.transcribe import TranscriptionService

class AIEvaluator:
    """Evaluator for AI features in the video summarizer."""
    
    def __init__(self):
        self.llm_ranker = LLMRanker()
        self.transcriber = TranscriptionService()
        
    def create_sample_transcript(self) -> List[Dict[str, Any]]:
        """Create sample transcript data for evaluation."""
        return [
            {
                "start": 0.0,
                "end": 5.0,
                "text": "Welcome to our product launch. Today we're excited to announce our new AI-powered video summarization platform."
            },
            {
                "start": 5.0,
                "end": 10.0,
                "text": "This platform uses advanced machine learning to automatically create highlights from your videos."
            },
            {
                "start": 10.0,
                "end": 15.0,
                "text": "The key features include intelligent segment selection, dynamic clip duration, and comprehensive coverage."
            },
            {
                "start": 15.0,
                "end": 20.0,
                "text": "Our AI analyzes the entire video timeline to ensure you don't miss important content."
            },
            {
                "start": 20.0,
                "end": 25.0,
                "text": "The system is designed to be production-ready with robust error handling and comprehensive logging."
            },
            {
                "start": 25.0,
                "end": 30.0,
                "text": "Thank you for your attention. We're excited to see how this platform helps you create better video content."
            }
        ]
    
    def evaluate_llm_ranking(self, segments: List[Dict[str, Any]], target_seconds: int) -> Dict[str, Any]:
        """Evaluate LLM ranking performance."""
        print(f"🤖 Evaluating LLM ranking for {target_seconds}s target...")
        
        start_time = time.time()
        
        try:
            # Test LLM ranking
            selected_segments = self.llm_ranker.rank_segments(segments, target_seconds)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Calculate metrics
            total_duration = sum(seg["end"] - seg["start"] for seg in selected_segments)
            segment_count = len(selected_segments)
            duration_accuracy = abs(total_duration - target_seconds) / target_seconds
            
            return {
                "success": True,
                "processing_time": processing_time,
                "selected_segments": len(selected_segments),
                "total_duration": total_duration,
                "target_duration": target_seconds,
                "duration_accuracy": 1 - duration_accuracy,
                "segments": selected_segments
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time
            }
    
    def evaluate_temporal_diversity(self, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluate temporal diversity of selected segments."""
        if not segments:
            return {"diversity_score": 0.0, "coverage": "No segments"}
        
        # Calculate time distribution
        video_duration = max(seg["end"] for seg in segments)
        segment_starts = [seg["start"] for seg in segments]
        
        # Divide into thirds
        third = video_duration / 3
        beginning_segments = [s for s in segment_starts if s < third]
        middle_segments = [s for s in segment_starts if third <= s < 2 * third]
        end_segments = [s for s in segment_starts if s >= 2 * third]
        
        # Calculate diversity score
        coverage = len([x for x in [beginning_segments, middle_segments, end_segments] if x])
        diversity_score = coverage / 3.0
        
        return {
            "diversity_score": diversity_score,
            "coverage": f"{coverage}/3 time zones",
            "beginning_segments": len(beginning_segments),
            "middle_segments": len(middle_segments),
            "end_segments": len(end_segments)
        }
    
    def run_evaluation(self) -> Dict[str, Any]:
        """Run complete AI evaluation."""
        print("🎯 Starting AI Feature Evaluation...")
        print("=" * 50)
        
        # Create sample data
        segments = self.create_sample_transcript()
        print(f"📝 Created sample transcript with {len(segments)} segments")
        
        # Test different target durations
        test_cases = [60, 120, 180]
        results = {}
        
        for target_seconds in test_cases:
            print(f"\n🎬 Testing {target_seconds}s target duration...")
            
            # Evaluate LLM ranking
            llm_result = self.evaluate_llm_ranking(segments, target_seconds)
            
            if llm_result["success"]:
                # Evaluate temporal diversity
                diversity_result = self.evaluate_temporal_diversity(llm_result["segments"])
                
                results[f"{target_seconds}s"] = {
                    "llm_performance": llm_result,
                    "temporal_diversity": diversity_result,
                    "overall_score": (
                        llm_result["duration_accuracy"] * 0.6 + 
                        diversity_result["diversity_score"] * 0.4
                    )
                }
                
                print(f"✅ Success: {llm_result['selected_segments']} segments, "
                      f"{llm_result['total_duration']:.1f}s duration, "
                      f"{llm_result['processing_time']:.2f}s processing time")
                print(f"📊 Diversity: {diversity_result['diversity_score']:.2f} "
                      f"({diversity_result['coverage']})")
            else:
                results[f"{target_seconds}s"] = {
                    "error": llm_result["error"],
                    "success": False
                }
                print(f"❌ Failed: {llm_result['error']}")
        
        # Calculate overall metrics
        successful_tests = [r for r in results.values() if r.get("success", False)]
        overall_score = sum(r["overall_score"] for r in successful_tests) / len(successful_tests) if successful_tests else 0
        
        evaluation_summary = {
            "timestamp": datetime.now().isoformat(),
            "test_cases": len(test_cases),
            "successful_tests": len(successful_tests),
            "overall_score": overall_score,
            "results": results,
            "recommendations": self._generate_recommendations(results)
        }
        
        return evaluation_summary
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on evaluation results."""
        recommendations = []
        
        successful_tests = [r for r in results.values() if r.get("success", False)]
        
        if not successful_tests:
            recommendations.append("❌ All tests failed - check API configuration and dependencies")
            return recommendations
        
        # Check duration accuracy
        duration_accuracies = [r["llm_performance"]["duration_accuracy"] for r in successful_tests]
        avg_accuracy = sum(duration_accuracies) / len(duration_accuracies)
        
        if avg_accuracy < 0.8:
            recommendations.append("⚠️ Duration accuracy is low - consider improving segment selection algorithm")
        else:
            recommendations.append("✅ Duration accuracy is good")
        
        # Check temporal diversity
        diversity_scores = [r["temporal_diversity"]["diversity_score"] for r in successful_tests]
        avg_diversity = sum(diversity_scores) / len(diversity_scores)
        
        if avg_diversity < 0.6:
            recommendations.append("⚠️ Temporal diversity is low - consider implementing chunk-based selection")
        else:
            recommendations.append("✅ Temporal diversity is good")
        
        # Check processing time
        processing_times = [r["llm_performance"]["processing_time"] for r in successful_tests]
        avg_time = sum(processing_times) / len(processing_times)
        
        if avg_time > 10:
            recommendations.append("⚠️ Processing time is high - consider implementing caching or optimization")
        else:
            recommendations.append("✅ Processing time is acceptable")
        
        return recommendations

def main():
    """Main evaluation function."""
    print("🎬 Video Summarizer AI Feature Evaluation")
    print("=" * 50)
    
    evaluator = AIEvaluator()
    results = evaluator.run_evaluation()
    
    print("\n" + "=" * 50)
    print("📊 EVALUATION SUMMARY")
    print("=" * 50)
    
    print(f"Test Cases: {results['test_cases']}")
    print(f"Successful: {results['successful_tests']}")
    print(f"Overall Score: {results['overall_score']:.2f}")
    
    print("\n📋 Recommendations:")
    for rec in results['recommendations']:
        print(f"  {rec}")
    
    # Save results to file
    output_file = "ai_evaluation_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")
    
    return results

if __name__ == "__main__":
    main()
