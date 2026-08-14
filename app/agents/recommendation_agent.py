"""The recommendation pipeline: retrieves candidates, decides whether to expand the pool
if scores are weak, scores everything, reranks if the pool's big enough, and trims to
top_n. Every step gets logged to RecommendationRun so a run can be replayed later."""

import json
import logging
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from sqlalchemy import Float, select
from sqlalchemy.orm import Session

from app.models.job import Job, JobSkill
from app.models.user import UserProfile
from app.models.recommendation import Recommendation
from app.models.recommendation_run import RecommendationRun
from app.services.embedding import build_profile_text, generate_embedding
from app.services.recommendation import compute_match_score, MatchBreakdown
from app.services.reranker import is_reranker_available, rerank_candidates
from app.services.scoring_config import load_weights
from app.services.feedback_loop import FeedbackLoop

logger = logging.getLogger(__name__)

# Agent behaviour parameters
INITIAL_CANDIDATE_POOL = 30
EXPANDED_CANDIDATE_POOL = 80
QUALITY_THRESHOLD = 0.35
MIN_ACCEPTABLE_SCORE = 0.15
RERANK_THRESHOLD = 20
MIN_SIMILARITY_THRESHOLD = 0.15

# Jobs below this quality score don't get recommended. Set from the real score
# distribution (min 38.75, avg 48.6, P25 44.75) - 40 catches the actually-bad
# postings without throwing out good ones.
MIN_JOB_QUALITY_SCORE = 40.0


class RecommendationAgent:
    """Pipeline that produces ranked, scored job recommendations
    for a user profile."""

    def __init__(self, db: Session):
        self.db = db

    def recommend(self, profile: UserProfile, top_n: int = 10, hard_constraints: dict | None = None) -> list[dict]:
        """Generate ranked recommendations for a user profile.

        """
        start_time = time.time()
        weights = load_weights()

        run = RecommendationRun(
            id=uuid.uuid4(),
            user_id=profile.user_id,
            retrieval_method="hnsw_semantic",
            embedding_model="BAAI/bge-base-en-v1.5",
            embedding_dim=768,
            reranker_model="cross-encoder/ms-marco-MiniLM-L-6-v2" if is_reranker_available() else None,
            scoring_config={
                "weights_version": weights.version,
                "weights": weights.to_dict(),
                "initial_pool": INITIAL_CANDIDATE_POOL,
                "expanded_pool": EXPANDED_CANDIDATE_POOL,
                "quality_threshold": QUALITY_THRESHOLD,
                "min_acceptable_score": MIN_ACCEPTABLE_SCORE,
                "rerank_threshold": RERANK_THRESHOLD,
                "hard_constraints": hard_constraints,
            },
        )

        decisions: list[dict] = []

        # Step 1 - ensure profile embedding exists
        if profile.profile_embedding is None:
            profile.profile_embedding = self._compute_profile_embedding(profile)
            self.db.commit()
            decisions.append({"step": "compute_embedding", "action": "computed_profile_embedding"})

        # Step 2 - initial retrieval
        candidates, similarities = self._retrieve_candidates(profile, limit=INITIAL_CANDIDATE_POOL)
        run.candidate_pool_size = len(candidates)
        decisions.append({"step": "retrieve", "pool_size": len(candidates), "method": "hnsw_cosine"})

        if not candidates:
            run.status = "completed"
            run.completed_at = datetime.now(timezone.utc)
            run.agent_decisions = {"decisions": decisions}
            run.latency_ms = (time.time() - start_time) * 1000
            self.db.add(run)
            self.db.commit()
            return []

        # Step 3 - score initial pool with hard constraints
        scored = self._score_candidates(profile, candidates, similarities, hard_constraints)
        decisions.append({
            "step": "score",
            "scored_count": len(scored),
            "hard_constraints_applied": hard_constraints is not None,
        })

        # Step 4 - expand the pool if the results we got aren't great
        passing = [s for s in scored if s["breakdown"].passes_hard_filters]
        avg_score = (sum(s["breakdown"].overall_score for s in passing) / len(passing)) if passing else 0.0

        if avg_score < QUALITY_THRESHOLD and len(candidates) < EXPANDED_CANDIDATE_POOL:
            logger.info(
                f"Agent: pool avg {avg_score:.2f} < {QUALITY_THRESHOLD}, "
                f"expanding to {EXPANDED_CANDIDATE_POOL}"
            )
            candidates, similarities = self._retrieve_candidates(profile, limit=EXPANDED_CANDIDATE_POOL)
            scored = self._score_candidates(profile, candidates, similarities, hard_constraints)
            run.candidate_pool_size = len(candidates)
            decisions.append({
                "step": "expand_pool",
                "trigger": "low_avg_score",
                "avg_score": round(avg_score, 4),
                "new_pool_size": len(candidates),
            })
        else:
            decisions.append({
                "step": "pool_quality_check",
                "avg_score": round(avg_score, 4),
                "action": "kept_initial_pool",
            })

        # Step 5 - filter, rerank, rank
        scored = [s for s in scored if s["breakdown"].passes_hard_filters]
        hard_filtered_count = len(scored)
        scored = [s for s in scored if s["breakdown"].overall_score >= MIN_ACCEPTABLE_SCORE]
        decisions.append({
            "step": "filter",
            "after_hard_filter": hard_filtered_count,
            "after_min_score": len(scored),
        })

        # Step 5b - collapse near-duplicate candidates (same company + near-identical
        # title) so the user isn't shown the same job twice under different postings.
        before_collapse = len(scored)
        scored = self._collapse_duplicate_candidates(scored)
        if len(scored) < before_collapse:
            decisions.append({
                "step": "collapse_duplicates",
                "before": before_collapse,
                "after": len(scored),
            })

        # Reranking decision
        if is_reranker_available() and len(scored) > RERANK_THRESHOLD:
            scored = self._rerank_scored(profile, scored)
            run.reranker_model = "cross-encoder/ms-marco-MiniLM-L-6-v2"
            decisions.append({
                "step": "rerank",
                "model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
                "reranked_count": len(scored),
            })
        else:
            decisions.append({
                "step": "rerank",
                "action": "skipped",
                "reason": "pool_too_small" if len(scored) <= RERANK_THRESHOLD else "model_unavailable",
            })

        scored.sort(key=lambda s: s["breakdown"].overall_score, reverse=True)
        final = scored[:top_n]
        run.final_pool_size = len(final)
        run.agent_decisions = {"decisions": decisions}

        # Persist
        self._persist_recommendations(profile, final, run)

        elapsed_ms = (time.time() - start_time) * 1000
        run.latency_ms = round(elapsed_ms, 1)
        run.status = "completed"
        run.completed_at = datetime.utcnow()
        self.db.commit()

        # Trigger instant email notification (fire-and-forget)
        if final:
            try:
                from app.services.notification_trigger import dispatch_notification_async
                dispatch_notification_async(profile.user_id)
            except Exception:
                logger.debug("Could not dispatch notification trigger", exc_info=True)

        return [
            {
                "job_id": str(item["job"].id),
                "title": item["job"].title_clean or item["job"].title,
                "company": item["job"].company,
                "location_city": item["job"].location_city,
                "location_country": item["job"].location_country,
                "remote": item["job"].remote,
                "salary_min": item["job"].salary_min,
                "salary_max": item["job"].salary_max,
                "salary_currency": item["job"].salary_currency,
                "category": item["job"].category,
                "job_type": item["job"].job_type,
                "url": item["job"].url,
                "rank": rank,
                "match_percentage": item["breakdown"].match_percentage,
                "breakdown": {
                    "semantic_similarity": round(item["breakdown"].semantic_similarity * 100, 1),
                    "skill_overlap": round(item["breakdown"].skill_overlap * 100, 1),
                    "location_fit": round(item["breakdown"].location_fit * 100, 1),
                    "salary_fit": round(item["breakdown"].salary_fit * 100, 1),
                    "experience_fit": round(item["breakdown"].experience_fit * 100, 1),
                    "job_type_fit": round(item["breakdown"].job_type_fit * 100, 1),
                    "recency_score": round(item["breakdown"].recency_score * 100, 1),
                },
                "matching_skills": item["breakdown"].matching_skills,
                "missing_skills": item["breakdown"].missing_skills,
                "recommendation_run_id": str(run.id),
            }
            for rank, item in enumerate(final, 1)
        ]

    def _compute_profile_embedding(self, profile: UserProfile) -> list[float]:
        """Turn the user profile into a vector representation - the same space as jobs."""
        text = build_profile_text(
            headline=profile.headline,
            skills=profile.skills,
            career_interests=profile.career_interests,
            experience_level=profile.experience_level,
        )
        return generate_embedding(text, is_query=True)

    def _retrieve_candidates(self, profile: UserProfile, limit: int) -> tuple[list[Job], list[float]]:
        """Vector search: find the `limit` jobs closest to the profile vector."""
        if profile.profile_embedding is None:
            return [], []

        # Use pgvector cosine distance for similarity scoring
        try:
            distance_expr = Job.embedding.op("<=>", return_type=Float)(profile.profile_embedding)
            stmt = (
                select(Job, distance_expr.label("distance"))
                .where(
                    Job.embedding.isnot(None),
                    Job.is_active.is_(True),
                    Job.quality_score.isnot(None),
                    Job.quality_score >= MIN_JOB_QUALITY_SCORE,
                )
                .order_by(distance_expr.asc())
                .limit(limit)
            )
            results = self.db.execute(stmt).all()
            jobs = []
            similarities = []
            for row in results:
                sim = 1.0 - row.distance
                if sim < MIN_SIMILARITY_THRESHOLD:
                    break
                jobs.append(row[0])
                similarities.append(sim)
            return jobs, similarities
        except Exception:
            pass

        # Fallback: Python cosine similarity
        import numpy as np

        stmt = (
            select(Job)
            .where(
                Job.embedding.isnot(None),
                Job.is_active.is_(True),
                Job.quality_score.isnot(None),
                Job.quality_score >= MIN_JOB_QUALITY_SCORE,
            )
        )

        all_jobs = self.db.execute(stmt).scalars().all()

        q_vec = np.array(profile.profile_embedding, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm == 0:
            return [], []

        scored = []
        for job in all_jobs:
            emb = job.embedding
            if emb is None:
                continue
            emb_vec = np.array(emb, dtype=np.float32)
            emb_norm = np.linalg.norm(emb_vec)
            if emb_norm == 0:
                continue
            sim = float(np.dot(q_vec, emb_vec) / (q_norm * emb_norm))
            scored.append((job, sim))

        scored.sort(key=lambda x: x[1], reverse=True)
        scored = [(j, s) for j, s in scored if s >= MIN_SIMILARITY_THRESHOLD]
        scored = scored[:limit]

        jobs = [item[0] for item in scored]
        similarities = [item[1] for item in scored]

        return jobs, similarities

    def _collapse_duplicate_candidates(self, scored: list[dict]) -> list[dict]:
        """Drop duplicate postings of the same job (same company + near-identical title,
        same thresholds as services/search.py) so we don't recommend it twice."""
        from rapidfuzz import fuzz
        from app.services.search import _normalise_company, _normalise_title

        groups: list[list[int]] = []
        assigned: set[int] = set()

        for i, item_i in enumerate(scored):
            if i in assigned:
                continue
            group = [i]
            norm_comp_i = _normalise_company(item_i["job"].company)
            norm_title_i = _normalise_title(item_i["job"].title_clean or item_i["job"].title)

            for j in range(i + 1, len(scored)):
                if j in assigned:
                    continue
                item_j = scored[j]
                norm_comp_j = _normalise_company(item_j["job"].company)
                norm_title_j = _normalise_title(item_j["job"].title_clean or item_j["job"].title)

                comp_sim = fuzz.token_set_ratio(norm_comp_i, norm_comp_j) / 100.0
                if comp_sim < 0.80:
                    continue
                title_sim = fuzz.token_set_ratio(norm_title_i, norm_title_j) / 100.0
                if title_sim < 0.60:
                    continue

                group.append(j)
                assigned.add(j)

            assigned.add(i)
            groups.append(group)

        collapsed = []
        for group in groups:
            best_idx = max(
                group,
                key=lambda idx: (
                    scored[idx]["breakdown"].overall_score,
                    scored[idx]["job"].quality_score or 0.0,
                ),
            )
            collapsed.append(scored[best_idx])

        return collapsed

    def _score_candidates(
        self, profile: UserProfile, candidates: list[Job], similarities: list[float],
        hard_constraints: dict | None = None,
    ) -> list[dict]:
        """Score every candidate job against the profile using pre-computed similarities.
        
        Applies feedback loop adjustments based on user's interaction history.
        """
        # Batch-fetch all skills in one query (avoids N+1)
        all_job_ids = [job.id for job in candidates]
        all_skills = self.db.query(JobSkill).filter(JobSkill.job_id.in_(all_job_ids)).all()
        skills_map: dict[uuid.UUID, list[str]] = defaultdict(list)
        for s in all_skills:
            skills_map[s.job_id].append(s.skill)

        # Get feedback adjustments for this user
        feedback_loop = FeedbackLoop(self.db)
        adjustments = feedback_loop.get_user_adjustments(profile.user_id)

        results = []
        for job, similarity in zip(candidates, similarities):
            job_skills = skills_map.get(job.id, [])

            breakdown = compute_match_score(
                profile, job, job_skills, similarity,
                profile.preferred_job_types,
                hard_constraints=hard_constraints,
            )

            # Apply feedback-based adjustments if we have enough data
            if adjustments.num_interactions >= 5:
                adjusted_score = feedback_loop.apply_feedback_boost(
                    profile.user_id, job, breakdown.overall_score, adjustments
                )
                breakdown.overall_score = adjusted_score
                breakdown.match_percentage = round(adjusted_score * 100, 1)

            results.append({"job": job, "breakdown": breakdown})

        return results

    def _rerank_scored(self, profile: UserProfile, scored: list[dict]) -> list[dict]:
        """Apply cross-encoder reranking to scored candidates."""
        query_text = build_profile_text(
            headline=profile.headline,
            skills=profile.skills,
            career_interests=profile.career_interests,
            experience_level=profile.experience_level,
        )

        # Batch-fetch skills for all candidates (avoids N+1)
        all_job_ids = [item["job"].id for item in scored]
        all_skills = self.db.query(JobSkill).filter(JobSkill.job_id.in_(all_job_ids)).all()
        skills_map: dict[uuid.UUID, list[str]] = defaultdict(list)
        for s in all_skills:
            skills_map[s.job_id].append(s.skill)

        candidate_dicts = []
        for item in scored:
            job = item["job"]
            candidate_dicts.append({
                "title": job.title_clean or job.title,
                "company": job.company or "",
                "location_city": job.location_city or "",
                "location_country": job.location_country or "",
                "skills": skills_map.get(job.id, []),
                "description": job.description or "",
                "_original_item": item,
            })

        reranked = rerank_candidates(query_text, candidate_dicts, score_field="title")

        results = []
        for cand in reranked:
            item = cand["_original_item"]
            rerank_norm = max(0, min(1, (cand.get("rerank_score", 0) + 10) / 20))
            pre_rerank_score = item["breakdown"].overall_score
            blended = 0.7 * pre_rerank_score + 0.3 * rerank_norm
            item["breakdown"].overall_score = blended
            item["breakdown"].match_percentage = round(blended * 100, 1)
            item["rerank_adjustment"] = round(blended - pre_rerank_score, 4)
            results.append(item)

        return results

    def _persist_recommendations(self, profile: UserProfile, scored: list[dict], run: RecommendationRun):
        """Save recommendations to the database, replacing any previous set."""
        self.db.query(Recommendation).filter(
            Recommendation.user_id == profile.user_id
        ).delete()

        for rank, item in enumerate(scored, 1):
            self.db.add(Recommendation(
                id=uuid.uuid4(),
                user_id=profile.user_id,
                job_id=item["job"].id,
                match_score=item["breakdown"].overall_score,
                rank=rank,
                score_breakdown={
                    "semantic": round(item["breakdown"].semantic_similarity, 4),
                    "skills": round(item["breakdown"].skill_overlap, 4),
                    "location": round(item["breakdown"].location_fit, 4),
                    "salary": round(item["breakdown"].salary_fit, 4),
                    "experience": round(item["breakdown"].experience_fit, 4),
                    "job_type": round(item["breakdown"].job_type_fit, 4),
                    "recency": round(item["breakdown"].recency_score, 4),
                },
                retrieval_method="hnsw_semantic",
                candidate_pool_position=rank,
                recommendation_run_id=run.id,
                explanation=None,
            ))

        self.db.add(run)
        self.db.commit()
