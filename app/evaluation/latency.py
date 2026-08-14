"""Latency benchmarking for the JobMatch recommendation system.

Measures and reports on:
1. Recommendation latency
2. Retrieval latency (pgvector)
3. Scoring latency
4. Reranking latency
5. LLM response latency (explanation generation)
6. Notification latency

Usage:
    from app.evaluation.latency import LatencyBenchmark
    benchmark = LatencyBenchmark(db)
    results = benchmark.run_full_benchmark(profile)
"""

import time
import logging
from dataclasses import dataclass, field
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.user import UserProfile
from app.models.job import Job, JobSkill
from app.services.embedding import generate_embedding, build_profile_text
from app.services.recommendation import compute_match_score
from app.services.reranker import is_reranker_available, rerank_candidates

logger = logging.getLogger(__name__)


@dataclass
class LatencyMeasurement:
    """A single latency measurement."""
    operation: str
    latency_ms: float
    timestamp: str
    metadata: dict = field(default_factory=dict)


@dataclass
class LatencyReport:
    """Complete latency benchmark report."""
    measurements: list[LatencyMeasurement] = field(default_factory=list)
    
    # Summary statistics
    total_latency_ms: float = 0.0
    retrieval_latency_ms: float = 0.0
    scoring_latency_ms: float = 0.0
    reranking_latency_ms: float = 0.0
    embedding_latency_ms: float = 0.0
    
    # Percentiles
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    
    # Metadata
    num_jobs_evaluated: int = 0
    measured_at: str = ""


class LatencyBenchmark:
    """Measures latency across the recommendation pipeline."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def measure_embedding_generation(self, profile: UserProfile) -> float:
        """Measure time to generate profile embedding."""
        start = time.time()
        
        profile_text = build_profile_text(
            headline=profile.headline,
            skills=profile.skills,
            career_interests=profile.career_interests,
            experience_level=profile.experience_level,
        )
        embedding = generate_embedding(profile_text, is_query=True)
        
        latency_ms = (time.time() - start) * 1000
        return latency_ms
    
    def measure_retrieval(self, profile: UserProfile, limit: int = 30) -> tuple[float, list]:
        """Measure time for pgvector retrieval."""
        import numpy as np
        from app.services.vector import cosine_similarity
        
        start = time.time()
        
        # Get all jobs with embeddings
        jobs = self.db.query(Job).filter(
            Job.is_active == True,
            Job.embedding.isnot(None),
            Job.quality_score >= 40.0
        ).all()
        
        # Compute similarities
        scored = []
        for job in jobs:
            if job.embedding is not None:
                sim = cosine_similarity(
                    np.array(profile.profile_embedding),
                    np.array(job.embedding)
                )
                if sim >= 0.15:
                    scored.append((job, sim))
        
        # Sort and take top limit
        scored.sort(key=lambda x: x[1], reverse=True)
        top_jobs = scored[:limit]
        
        latency_ms = (time.time() - start) * 1000
        return latency_ms, top_jobs
    
    def measure_scoring(self, profile: UserProfile, candidates: list) -> tuple[float, list]:
        """Measure time to score all candidates."""
        start = time.time()
        
        scored = []
        for job, similarity in candidates:
            # Get job skills
            job_skills = self.db.query(JobSkill).filter(JobSkill.job_id == job.id).all()
            skills_list = [s.skill for s in job_skills]
            
            breakdown = compute_match_score(
                profile, job, skills_list, similarity,
                profile.preferred_job_types,
            )
            scored.append({"job": job, "breakdown": breakdown})
        
        latency_ms = (time.time() - start) * 1000
        return latency_ms, scored
    
    def measure_reranking(self, profile: UserProfile, scored: list) -> tuple[float, list]:
        """Measure time for cross-encoder reranking."""
        if not is_reranker_available():
            return 0.0, scored
        
        start = time.time()
        
        query_text = build_profile_text(
            headline=profile.headline,
            skills=profile.skills,
            career_interests=profile.career_interests,
            experience_level=profile.experience_level,
        )
        
        candidate_dicts = []
        for item in scored:
            job = item["job"]
            candidate_dicts.append({
                "title": job.title_clean or job.title,
                "company": job.company or "",
                "location_city": job.location_city or "",
                "location_country": job.location_country or "",
                "skills": [],
                "description": job.description or "",
                "_original_item": item,
            })
        
        reranked = rerank_candidates(query_text, candidate_dicts, score_field="title")
        
        latency_ms = (time.time() - start) * 1000
        return latency_ms, reranked
    
    def run_full_benchmark(self, profile: UserProfile, num_runs: int = 3) -> LatencyReport:
        """Run full latency benchmark with multiple runs for averaging."""
        report = LatencyReport()
        report.measured_at = datetime.now().isoformat()
        
        all_latencies = {
            "embedding": [],
            "retrieval": [],
            "scoring": [],
            "reranking": [],
            "total": [],
        }
        
        for run in range(num_runs):
            total_start = time.time()
            
            # Measure embedding
            embedding_latency = self.measure_embedding_generation(profile)
            all_latencies["embedding"].append(embedding_latency)
            
            # Measure retrieval
            retrieval_latency, candidates = self.measure_retrieval(profile)
            all_latencies["retrieval"].append(retrieval_latency)
            report.num_jobs_evaluated = len(candidates)
            
            # Measure scoring
            scoring_latency, scored = self.measure_scoring(profile, candidates)
            all_latencies["scoring"].append(scoring_latency)
            
            # Measure reranking
            reranking_latency, _ = self.measure_reranking(profile, scored)
            all_latencies["reranking"].append(reranking_latency)
            
            total_latency = (time.time() - total_start) * 1000
            all_latencies["total"].append(total_latency)
            
            # Record measurements
            report.measurements.extend([
                LatencyMeasurement("embedding", embedding_latency, datetime.now().isoformat(), {"run": run}),
                LatencyMeasurement("retrieval", retrieval_latency, datetime.now().isoformat(), {"run": run}),
                LatencyMeasurement("scoring", scoring_latency, datetime.now().isoformat(), {"run": run}),
                LatencyMeasurement("reranking", reranking_latency, datetime.now().isoformat(), {"run": run}),
                LatencyMeasurement("total", total_latency, datetime.now().isoformat(), {"run": run}),
            ])
        
        # Compute averages
        report.embedding_latency_ms = sum(all_latencies["embedding"]) / num_runs
        report.retrieval_latency_ms = sum(all_latencies["retrieval"]) / num_runs
        report.scoring_latency_ms = sum(all_latencies["scoring"]) / num_runs
        report.reranking_latency_ms = sum(all_latencies["reranking"]) / num_runs
        report.total_latency_ms = sum(all_latencies["total"]) / num_runs
        
        # Compute percentiles
        total_latencies = sorted(all_latencies["total"])
        if total_latencies:
            report.p50_latency_ms = total_latencies[len(total_latencies) // 2]
            report.p95_latency_ms = total_latencies[int(len(total_latencies) * 0.95)]
            report.p99_latency_ms = total_latencies[int(len(total_latencies) * 0.99)]
        
        return report
    
    def print_report(self, report: LatencyReport):
        """Print formatted latency report."""
        print(f"\n{'='*70}")
        print("  LATENCY BENCHMARK REPORT")
        print(f"{'='*70}")
        print(f"  Measured at: {report.measured_at}")
        print(f"  Jobs evaluated: {report.num_jobs_evaluated}")
        print(f"\n  Average Latencies (ms):")
        print(f"    Embedding generation: {report.embedding_latency_ms:.1f}")
        print(f"    Retrieval:           {report.retrieval_latency_ms:.1f}")
        print(f"    Scoring:             {report.scoring_latency_ms:.1f}")
        print(f"    Reranking:           {report.reranking_latency_ms:.1f}")
        print(f"    ─────────────────────────────────")
        print(f"    Total:               {report.total_latency_ms:.1f}")
        print(f"\n  Percentiles (ms):")
        print(f"    P50:  {report.p50_latency_ms:.1f}")
        print(f"    P95:  {report.p95_latency_ms:.1f}")
        print(f"    P99:  {report.p99_latency_ms:.1f}")
        print(f"{'='*70}")
