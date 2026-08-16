"""Recommendation scoring weights, versioned so results stay reproducible. Default
weights live in code (v1.0); other versions can be loaded from a JSON config file
for experimenting without touching code."""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).parent.parent.parent / "config"


@dataclass
class ScoringWeights:
    """A named, versioned set of scoring weights."""
    version: str = "v3.0"
    semantic: float = 0.25
    skills: float = 0.30
    location: float = 0.15
    salary: float = 0.12
    experience: float = 0.08
    job_type: float = 0.05
    recency: float = 0.05

    def to_dict(self) -> dict[str, float]:
        return {
            "semantic": self.semantic,
            "skills": self.skills,
            "location": self.location,
            "salary": self.salary,
            "experience": self.experience,
            "job_type": self.job_type,
            "recency": self.recency,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ScoringWeights":
        return cls(
            version=data.get("version", "custom"),
            semantic=data.get("semantic", 0.25),
            skills=data.get("skills", 0.25),
            location=data.get("location", 0.15),
            salary=data.get("salary", 0.15),
            experience=data.get("experience", 0.10),
            job_type=data.get("job_type", 0.05),
            recency=data.get("recency", 0.05),
        )


# Default weights - the version used in production
DEFAULT_WEIGHTS = ScoringWeights()


def load_weights(version: str | None = None) -> ScoringWeights:
    """Load scoring weights by version.

    Args:
        version: Weight version to load. If None, returns DEFAULT_WEIGHTS.
            If "v1.0", returns DEFAULT_WEIGHTS.
            Otherwise looks for config/scoring_{version}.json.

    Returns:
        ScoringWeights instance.
    """
    if version is None or version == "v3.0":
        return DEFAULT_WEIGHTS

    config_file = CONFIG_DIR / f"scoring_{version}.json"
    if not config_file.exists():
        logger.warning(f"Weight config {config_file} not found, using defaults")
        return DEFAULT_WEIGHTS

    try:
        with open(config_file) as f:
            data = json.load(f)
        weights = ScoringWeights.from_dict(data)
        logger.info(f"Loaded scoring weights version {version} from {config_file}")
        return weights
    except Exception as e:
        logger.error(f"Failed to load weight config: {e}. Using defaults.")
        return DEFAULT_WEIGHTS


def save_weights(weights: ScoringWeights) -> Path:
    """Save a scoring weight configuration to disk."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"scoring_{weights.version}.json"
    path = CONFIG_DIR / filename

    with open(path, "w") as f:
        json.dump({"version": weights.version, **weights.to_dict()}, f, indent=2)

    logger.info(f"Saved scoring weights to {path}")
    return path


# Pre-defined experimental weight sets for ablation studies
ABLATION_WEIGHTS = {
    "semantic_only": ScoringWeights(
        version="ablation_semantic_only",
        semantic=1.0, skills=0.0, location=0.0,
        salary=0.0, experience=0.0, job_type=0.0, recency=0.0,
    ),
    "skills_only": ScoringWeights(
        version="ablation_skills_only",
        semantic=0.0, skills=1.0, location=0.0,
        salary=0.0, experience=0.0, job_type=0.0, recency=0.0,
    ),
    "no_semantic": ScoringWeights(
        version="ablation_no_semantic",
        semantic=0.0, skills=0.35, location=0.20,
        salary=0.20, experience=0.15, job_type=0.05, recency=0.05,
    ),
    "balanced": ScoringWeights(
        version="balanced",
        semantic=0.20, skills=0.25, location=0.15,
        salary=0.15, experience=0.10, job_type=0.05, recency=0.10,
    ),
}
