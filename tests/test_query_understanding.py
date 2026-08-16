"""Tests for query understanding (LLM query intent classification + expansion).

Tests the basic analysis (regex-based fast path) and verifies fallback
behaviour when the LLM is unavailable.

Run:
    python -m pytest tests/test_query_understanding.py -v
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.query_understanding import (
    analyse_query,
    QueryAnalysis,
    _basic_analysis,
    _parse_response,
)


class TestBasicAnalysis:
    """Test the regex-based fast path that avoids LLM calls."""

    def test_single_known_skill(self):
        result = _basic_analysis("python")
        assert result is not None
        assert result.intent == "skill_search"
        assert "python" in result.expanded_terms
        assert result.confidence >= 0.8

    def test_skill_with_suffix(self):
        result = _basic_analysis("react developer")
        assert result is not None
        assert result.intent == "skill_search"
        assert "react" in result.expanded_terms

    def test_remote_location(self):
        result = _basic_analysis("remote jobs in London")
        assert result is not None
        assert result.intent == "location_search"
        assert "london" in result.extracted_location.lower()

    def test_empty_query(self):
        result = analyse_query("")
        assert result.intent == "hybrid"
        assert result.raw_query == ""

    def test_non_technical_query_returns_none(self):
        result = _basic_analysis("best companies to work for in 2024")
        assert result is None


class TestAnalyseQuery:
    """Test the main analyse_query function."""

    def test_empty_query_returns_default(self):
        result = analyse_query("")
        assert isinstance(result, QueryAnalysis)
        assert result.intent == "hybrid"

    def test_known_skill_uses_fast_path(self):
        result = analyse_query("python")
        assert result.intent == "skill_search"
        assert result.confidence >= 0.8

    def test_cache_works(self):
        r1 = analyse_query("docker", use_cache=True)
        r2 = analyse_query("docker", use_cache=True)
        assert r1.intent == r2.intent

    @patch("app.services.query_understanding._get_client")
    def test_llm_called_for_complex_query(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"intent": "hybrid", "expanded_terms": ["distributed systems", "microservices"], "confidence": 0.9}'
        mock_client.chat.completions.create.return_value = mock_response

        # Clear cache to ensure LLM is called
        from app.services.query_understanding import _cache
        _cache.clear()

        # A query that won't match basic patterns (no known skill, no "developer/engineer" suffix)
        result = analyse_query("distributed systems at FAANG companies", use_cache=False)
        assert result.intent == "hybrid"
        assert "distributed systems" in result.expanded_terms
        mock_client.chat.completions.create.assert_called_once()

    @patch("app.services.query_understanding._get_client")
    def test_llm_failure_falls_back(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API error")

        result = analyse_query("kubernetes architect", use_cache=False)
        # Should fall back to basic analysis
        assert isinstance(result, QueryAnalysis)


class TestParseResponse:
    """Test JSON parsing from LLM responses."""

    def test_clean_json(self):
        raw = '{"intent": "skill_search", "expanded_terms": ["python", "django"], "confidence": 0.9}'
        result = _parse_response(raw)
        assert result["intent"] == "skill_search"
        assert "python" in result["expanded_terms"]

    def test_markdown_fenced_json(self):
        raw = '```json\n{"intent": "skill_search", "expanded_terms": [], "confidence": 0.7}\n```'
        result = _parse_response(raw)
        assert result["intent"] == "skill_search"

    def test_json_with_surrounding_text(self):
        raw = 'Here is the analysis: {"intent": "hybrid", "expanded_terms": [], "confidence": 0.5} hope this helps!'
        result = _parse_response(raw)
        assert result["intent"] == "hybrid"

    def test_invalid_json_returns_empty(self):
        result = _parse_response("not json at all")
        assert result == {}
