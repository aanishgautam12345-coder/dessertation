"""Tests for LLM-based result re-scoring.

Tests score application logic, caching, and fallback behaviour
when the LLM is unavailable.

Run:
    python -m pytest tests/test_llm_reranker.py -v
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.llm_reranker import (
    llm_rerank,
    LLMRerankResult,
    _apply_scores,
    _parse_response,
    _cache_key,
)


class TestApplyScores:
    """Test the score application and blending logic."""

    def test_blending_with_llm_score(self):
        candidates = [
            {"id": "1", "title": "Job A", "ranking_score": 80},
            {"id": "2", "title": "Job B", "ranking_score": 60},
        ]
        llm_results = [
            LLMRerankResult(job_id="1", llm_score=0.9, reason="Great match"),
            LLMRerankResult(job_id="2", llm_score=0.3, reason="Poor match"),
        ]
        result = _apply_scores(candidates, llm_results, blend_weight=0.4, top_n=None)

        # Job A: 0.6 * 0.8 + 0.4 * 0.9 = 0.48 + 0.36 = 0.84 -> 84.0
        assert result[0]["id"] == "1"
        assert result[0]["blended_score"] == 84.0
        assert result[0]["llm_score"] == 0.9

        # Job B: 0.6 * 0.6 + 0.4 * 0.3 = 0.36 + 0.12 = 0.48 -> 48.0
        assert result[1]["id"] == "2"
        assert result[1]["blended_score"] == 48.0

    def test_missing_llm_score_preserves_original(self):
        candidates = [
            {"id": "1", "title": "Job A", "ranking_score": 80},
            {"id": "2", "title": "Job B", "ranking_score": 60},
        ]
        llm_results = [
            LLMRerankResult(job_id="1", llm_score=0.9, reason="Great match"),
        ]
        result = _apply_scores(candidates, llm_results, blend_weight=0.4, top_n=None)

        # Job B has no LLM score, should keep original
        job_b = next(r for r in result if r["id"] == "2")
        assert job_b["llm_score"] is None
        assert job_b["blended_score"] == 60

    def test_top_n_limit(self):
        candidates = [
            {"id": str(i), "title": f"Job {i}", "ranking_score": 90 - i * 10}
            for i in range(5)
        ]
        llm_results = [
            LLMRerankResult(job_id=str(i), llm_score=0.5, reason="ok")
            for i in range(5)
        ]
        result = _apply_scores(candidates, llm_results, blend_weight=0.4, top_n=3)
        assert len(result) == 3

    def test_sorting_by_blended_score(self):
        candidates = [
            {"id": "1", "title": "Low", "ranking_score": 90},
            {"id": "2", "title": "High", "ranking_score": 50},
        ]
        llm_results = [
            LLMRerankResult(job_id="1", llm_score=0.1, reason=""),
            LLMRerankResult(job_id="2", llm_score=1.0, reason=""),
        ]
        result = _apply_scores(candidates, llm_results, blend_weight=0.5, top_n=None)
        # Job 2 should rank higher despite lower original score
        assert result[0]["id"] == "2"


class TestParseResponse:
    """Test JSON parsing from LLM rerank responses."""

    def test_valid_array(self):
        raw = '[{"job_id": "1", "score": 0.8, "reason": "Good match"}]'
        result = _parse_response(raw, [{"id": "1"}])
        assert len(result) == 1
        assert result[0].job_id == "1"
        assert result[0].llm_score == 0.8

    def test_markdown_fenced(self):
        raw = '```json\n[{"job_id": "1", "score": 0.5, "reason": "ok"}]\n```'
        result = _parse_response(raw, [{"id": "1"}])
        assert len(result) == 1

    def test_invalid_json(self):
        result = _parse_response("not json", [{"id": "1"}])
        assert result == []

    def test_score_clamping(self):
        raw = '[{"job_id": "1", "score": 1.5, "reason": "over"}, {"job_id": "2", "score": -0.5, "reason": "under"}]'
        result = _parse_response(raw, [{"id": "1"}, {"id": "2"}])
        assert result[0].llm_score == 1.0  # Clamped
        assert result[1].llm_score == 0.0  # Clamped


class TestCacheKey:
    """Test cache key generation."""

    def test_same_inputs_same_key(self):
        key1 = _cache_key("profile text", ["1", "2"])
        key2 = _cache_key("profile text", ["1", "2"])
        assert key1 == key2

    def test_different_inputs_different_key(self):
        key1 = _cache_key("profile A", ["1"])
        key2 = _cache_key("profile B", ["1"])
        assert key1 != key2


class TestLLMRerank:
    """Test the main llm_rerank function."""

    def test_empty_candidates(self):
        result = llm_rerank("profile", [])
        assert result == []

    def test_fallback_on_llm_failure(self):
        candidates = [{"id": "1", "title": "Job", "ranking_score": 75}]
        with patch("app.services.llm_reranker._get_client") as mock:
            mock.return_value = MagicMock()
            mock.return_value.chat.completions.create.side_effect = Exception("API down")
            result = llm_rerank("profile", candidates, use_cache=False)
            # Should fall back gracefully
            assert len(result) == 1
            assert result[0]["llm_score"] is None

    def test_cache_hit(self):
        candidates = [{"id": "1", "title": "Job", "ranking_score": 75}]
        # Prime the cache
        with patch("app.services.llm_reranker._get_client") as mock:
            mock_client = MagicMock()
            mock.return_value = mock_client
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = '[{"job_id": "1", "score": 0.8, "reason": "good"}]'
            mock_client.chat.completions.create.return_value = mock_response

            r1 = llm_rerank("profile", [dict(c) for c in candidates], use_cache=True)

        # Second call should hit cache (no LLM call)
        r2 = llm_rerank("profile", [dict(c) for c in candidates], use_cache=True)
        assert r1[0]["id"] == r2[0]["id"]
