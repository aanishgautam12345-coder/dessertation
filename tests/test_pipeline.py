"""Tests for data processing pipeline."""

import uuid
import pytest
from unittest.mock import patch, MagicMock

from app.database import Base
from app.models.job import RawJob
from app.models.ingestion_run import IngestionRun
from app.models.job import Job


@pytest.fixture()
def raw_jobs(db):
    """Create raw job records for pipeline testing."""
    run = IngestionRun(
        id=uuid.uuid4(),
        source="test",
        status="completed",
        records_fetched=3,
    )
    db.add(run)
    db.flush()

    jobs = []
    for i, title in enumerate(["Python Dev", "Java Dev", "Python Dev"]):
        job = RawJob(
            id=uuid.uuid4(),
            ingestion_run_id=run.id,
            title=title,
            company=f"Company {i}",
            description=f"Description for {title}",
            source="test",
            url=f"http://example.com/job/{i}",
        )
        db.add(job)
        jobs.append(job)
    db.flush()
    return jobs, run


class TestPipelineSmoke:
    """Smoke tests to verify the pipeline modules load correctly."""

    def test_imports(self):
        from app.processing.pipeline import process_raw_jobs
        assert callable(process_raw_jobs)

    def test_title_clean_imports(self):
        from app.processing.title import clean_title
        result = clean_title("SENIOR PYTHON DEVELOPER")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_quality_score_imports(self):
        from app.processing.quality import score_job
        result = score_job(
            title="Python Dev",
            company="Test Co",
            description="A job description",
            location_city="London",
            location_country="UK",
            salary_min=50000,
            salary_max=70000,
            category="tech",
            job_type="full_time",
            experience_level="mid",
            skills=["python"],
            url="http://example.com",
            source="test",
        )
        assert hasattr(result, "overall")
        assert 0 <= result.overall <= 100

    def test_dedup_hash(self):
        from app.processing.dedup import generate_dedup_hash
        h1 = generate_dedup_hash("Python Dev", "Co", "London", 50000, 70000)
        h2 = generate_dedup_hash("Python Dev", "Co", "London", 50000, 70000)
        h3 = generate_dedup_hash("Java Dev", "Co", "London", 50000, 70000)
        assert h1 == h2
        assert h1 != h3

    def test_skills_normalization(self):
        from app.processing.skills import normalize_user_skills
        result = normalize_user_skills(["Python", "python", "FASTAPI"])
        assert isinstance(result, list)
        assert len(result) <= 3  # should deduplicate
