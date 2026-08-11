"""Tests for embedding service."""

import pytest
from unittest.mock import patch, MagicMock
import numpy as np

from app.services.embedding import build_job_text, build_profile_text


class TestBuildJobText:
    def test_basic(self):
        result = build_job_text("Python Developer", "We need Python", None)
        assert "Python Developer" in result
        assert "We need Python" in result

    def test_with_skills(self):
        result = build_job_text("Dev", "Desc", ["python", "fastapi"])
        assert "python" in result
        assert "fastapi" in result

    def test_empty_description(self):
        result = build_job_text("Dev", "", None)
        assert "Dev" in result


class TestBuildProfileText:
    def test_basic(self):
        result = build_profile_text(
            headline="Backend Dev",
            skills=["python"],
            career_interests=None,
            experience_level=None,
        )
        assert "Backend Dev" in result
        assert "python" in result

    def test_all_fields(self):
        result = build_profile_text(
            headline="Backend Dev",
            skills=["python", "fastapi"],
            career_interests="Build APIs",
            experience_level="mid",
        )
        assert "Backend Dev" in result
        assert "python" in result
        assert "Build APIs" in result
        assert "mid" in result
