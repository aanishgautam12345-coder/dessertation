"""Baseline comparison systems for dissertation evaluation.

Implements three baseline approaches to compare against the proposed system:
1. KeywordSearchBaseline - TF-IDF/BM25 keyword matching
2. RuleBasedBaseline - Metadata-only weighted scoring (no embeddings)
3. EmbeddingOnlyBaseline - Pure cosine similarity (no metadata scoring)

Usage:
    from app.evaluation.baselines import KeywordSearchBaseline, RuleBasedBaseline
    baseline = KeywordSearchBaseline(db)
    results = baseline.search("python developer", limit=10)
"""

import re
import math
from collections import Counter
from dataclasses import dataclass
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.job import Job, JobSkill
from app.models.user import UserProfile
from app.services.recommendation import _score_skills, _score_location, _score_salary, _score_experience, _score_job_type, _score_recency, EXPERIENCE_ORDER


@dataclass
class BaselineResult:
    """Standardized result from any baseline system."""
    job_id: str
    title: str
    company: str | None
    score: float
    method: str
    explanation: str = ""


class KeywordSearchBaseline:
    """Baseline 1: TF-IDF/BM25 keyword matching.
    
    Uses PostgreSQL full-text search (tsvector/tsquery) to find jobs
    matching the query keywords. No semantic understanding, no personalization.
    """
    
    METHOD_NAME = "Keyword (BM25)"
    
    def __init__(self, db: Session):
        self.db = db
    
    def search(self, query: str, limit: int = 10) -> list[BaselineResult]:
        """Search using PostgreSQL full-text search."""
        # Build tsquery from user query
        tokens = self._tokenize(query)
        if not tokens:
            return []
        
        # Use PostgreSQL full-text search with tsvector
        tsquery = " & ".join(tokens)
        
        try:
            results = self.db.query(Job).filter(
                Job.is_active == True,
                Job.search_vector.op("@@")(
                    func.to_tsquery("english", tsquery)
                )
            ).order(
                func.ts_rank(Job.search_vector, func.to_tsquery("english", tsquery)).desc()
            ).limit(limit).all()
            
            return [
                BaselineResult(
                    job_id=str(job.id),
                    title=job.title,
                    company=job.company,
                    score=1.0 - (i / len(results)) if results else 0.0,
                    method=self.METHOD_NAME,
                    explanation=f"Keyword match for: {query}"
                )
                for i, job in enumerate(results)
            ]
        except Exception:
            # Fallback: simple ILIKE search if tsvector not available
            return self._fallback_search(query, limit)
    
    def _fallback_search(self, query: str, limit: int) -> list[BaselineResult]:
        """Fallback using ILIKE when full-text search fails."""
        tokens = self._tokenize(query)
        conditions = [
            Job.title.ilike(f"%{token}%") | 
            Job.description.ilike(f"%{token}%")
            for token in tokens
        ]
        
        results = self.db.query(Job).filter(
            Job.is_active == True,
            or_(*conditions)
        ).limit(limit).all()
        
        return [
            BaselineResult(
                job_id=str(job.id),
                title=job.title,
                company=job.company,
                score=1.0 - (i / len(results)) if results else 0.0,
                method=self.METHOD_NAME,
                explanation=f"Keyword match for: {query}"
            )
            for i, job in enumerate(results)
        ]
    
    def _tokenize(self, text: str) -> list[str]:
        """Simple tokenization: lowercase, split, remove stopwords."""
        stopwords = {
            "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "shall", "can", "to", "of", "in", "for",
            "on", "with", "at", "by", "from", "as", "into", "through", "during",
            "before", "after", "above", "below", "between", "out", "off", "over",
            "under", "again", "further", "then", "once", "here", "there", "when",
            "where", "why", "how", "all", "each", "every", "both", "few", "more",
            "most", "other", "some", "such", "no", "nor", "not", "only", "own",
            "same", "so", "than", "too", "very", "just", "because", "but", "and",
            "or", "if", "while", "about", "against", "up", "down"
        }
        
        words = re.findall(r'\w+', text.lower())
        return [w for w in words if w not in stopwords and len(w) > 1]


class RuleBasedBaseline:
    """Baseline 2: Rule-based weighted scoring (no embeddings).
    
    Uses the same multi-factor scoring as the proposed system but
    WITHOUT semantic embeddings. Only uses explicit metadata matching.
    """
    
    METHOD_NAME = "Rule-Based (No Embeddings)"
    
    def __init__(self, db: Session):
        self.db = db
    
    def search(self, profile: UserProfile, limit: int = 10) -> list[BaselineResult]:
        """Score all jobs using rule-based matching only."""
        from app.services.recommendation import compute_match_score
        
        jobs = self.db.query(Job).filter(
            Job.is_active == True,
            Job.quality_score >= 40.0
        ).all()
        
        scored = []
        for job in jobs:
            # Get job skills
            job_skills = self.db.query(JobSkill).filter(JobSkill.job_id == job.id).all()
            skills_list = [s.skill for s in job_skills]
            
            # Compute match score (without semantic similarity)
            # We'll use 0.5 as a neutral semantic score since we're not using embeddings
            breakdown = compute_match_score(
                profile=profile,
                job=job,
                job_skills=skills_list,
                semantic_similarity=0.5,  # Neutral - no embedding
                preferred_job_types=profile.preferred_job_types,
            )
            
            if breakdown.overall_score > 0.15:
                scored.append((job, breakdown.overall_score))
        
        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)
        
        return [
            BaselineResult(
                job_id=str(job.id),
                title=job.title,
                company=job.company,
                score=score,
                method=self.METHOD_NAME,
                explanation=f"Rule-based score: {score:.3f}"
            )
            for job, score in scored[:limit]
        ]


class EmbeddingOnlyBaseline:
    """Baseline 3: Pure cosine similarity (no metadata scoring).
    
    Uses only semantic embeddings for matching, without the multi-factor
    scoring formula. Tests whether embeddings alone are sufficient.
    """
    
    METHOD_NAME = "Embedding Only (No Metadata)"
    
    def __init__(self, db: Session):
        self.db = db
    
    def search(self, profile: UserProfile, limit: int = 10) -> list[BaselineResult]:
        """Search using only embedding similarity."""
        if profile.profile_embedding is None:
            return []
        
        import numpy as np
        from app.services.vector import cosine_similarity
        
        # Get all jobs with embeddings
        jobs = self.db.query(Job).filter(
            Job.is_active == True,
            Job.embedding.isnot(None),
            Job.quality_score >= 40.0
        ).all()
        
        scored = []
        for job in jobs:
            if job.embedding is not None:
                sim = cosine_similarity(
                    np.array(profile.profile_embedding),
                    np.array(job.embedding)
                )
                if sim >= 0.15:
                    scored.append((job, sim))
        
        # Sort by similarity descending
        scored.sort(key=lambda x: x[1], reverse=True)
        
        return [
            BaselineResult(
                job_id=str(job.id),
                title=job.title,
                company=job.company,
                score=sim,
                method=self.METHOD_NAME,
                explanation=f"Semantic similarity: {sim:.3f}"
            )
            for job, sim in scored[:limit]
        ]
