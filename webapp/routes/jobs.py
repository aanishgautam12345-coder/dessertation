"""Jobs Routes - search, recommendations, saved jobs, recent jobs."""

import uuid

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user

from app.database import SessionLocal
from app.models.job import Job, JobSkill
from app.models.user import UserProfile
from app.models.recommendation import SavedJob
from app.models.user import UserProfile
from app.services.search import evidence_search, semantic_search, keyword_search, hybrid_search, personalized_search, format_salary_display
from app.api.jobs_extended import search_by_company, search_by_skills
from app.agents.recommendation_agent import RecommendationAgent
from app.services.recommendation import compute_match_score
from app.services.rag import generate_explanation
from app.processing.category import CATEGORIES

jobs_bp = Blueprint("jobs", __name__, url_prefix="/jobs")


@jobs_bp.route("/search")
@login_required
def search():
    query = request.args.get("q", "").strip()
    country = request.args.get("country", "").strip()
    category = request.args.get("category", "")
    remote_only = request.args.get("remote_only") == "on"
    recommended = request.args.get("recommended") == "on"
    min_salary = request.args.get("min_salary", type=float)
    company_filter = request.args.get("company", "").strip()
    skills_filter = request.args.get("skills", "").strip()
    page = max(request.args.get("page", 1, type=int), 1)
    page_size = 20
    profile_message = None

    results = []
    if query or company_filter or skills_filter:
        db = SessionLocal()
        try:
            if not query and (company_filter or skills_filter):
                # No keyword query - search standalone by the Company/Skills
                # fields directly, since the general keyword box never
                # searches Job.company and only opportunistically catches
                # skills for short technical queries.
                if company_filter:
                    results = search_by_company(q=company_filter, limit=page * page_size, db=db)["results"]
                elif skills_filter:
                    results = search_by_skills(skills=skills_filter, match_all=False, limit=page * page_size, db=db)["results"]
                results = results[(page - 1) * page_size:]
            elif recommended:
                profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
                if not profile or profile.profile_embedding is None or (not profile.skills and not profile.headline):
                    profile_message = "Complete your profile before using Recommended for me."
                else:
                    from app.config import get_settings
                    results = personalized_search(
                        db, query, profile, location_country=country or None,
                        remote_only=remote_only, category=category or None,
                        min_salary=min_salary,
                        threshold=get_settings().recommended_search_threshold,
                        limit=page_size, offset=(page - 1) * page_size,
                    )
            elif country or category or remote_only or min_salary:
                results = hybrid_search(
                    db, query=query, location_country=country or None,
                    remote_only=remote_only, category=category or None,
                    min_salary=min_salary, limit=page * page_size,
                )
                results = results[(page - 1) * page_size:]
            else:
                results = evidence_search(db, query=query, limit=page * page_size, rerank=True)
                results = results[(page - 1) * page_size:]

            # Apply company filter (client-side on current results)
            if company_filter:
                results = [r for r in results if company_filter.lower() in (r.get("company") or "").lower()]

            # Apply skills filter (client-side on current results)
            if skills_filter:
                skill_terms = [s.strip().lower() for s in skills_filter.split(",") if s.strip()]
                if skill_terms:
                    filtered = []
                    for r in results:
                        job_skills = [s.skill.lower() for s in db.query(JobSkill).filter(JobSkill.job_id == r["id"]).all()]
                        if any(any(term in js for js in job_skills) for term in skill_terms):
                            filtered.append(r)
                    results = filtered

            saved_ids = {
                str(s.job_id) for s in
                db.query(SavedJob).filter(SavedJob.user_id == current_user.id).all()
            }
            for r in results:
                r["is_saved"] = r["id"] in saved_ids
                r["salary_display"] = format_salary_display(
                    r.get("salary_min"), r.get("salary_max"),
                    r.get("salary_currency"), r.get("salary_period"),
                )
        finally:
            db.close()

    return render_template(
        "main/search.html", query=query, results=results,
        categories=CATEGORIES, selected_category=category,
        country=country, remote_only=remote_only,
        recommended=recommended, min_salary=min_salary, page=page,
        profile_message=profile_message,
        company_filter=company_filter, skills_filter=skills_filter,
    )


@jobs_bp.route("/recommendations")
@login_required
def recommendations():
    db = SessionLocal()
    try:
        profile = current_user.profile

        if not profile or (not profile.skills and not profile.headline):
            return render_template("main/recommendations.html", recs=None, no_profile=True)

        agent = RecommendationAgent(db)
        recs = agent.recommend(profile, top_n=10)

        saved_ids = {
            str(s.job_id) for s in
            db.query(SavedJob).filter(SavedJob.user_id == current_user.id).all()
        }
        for r in recs:
            r["is_saved"] = r["job_id"] in saved_ids

        overview = _build_recommendation_overview(recs)

        return render_template(
            "main/recommendations.html", recs=recs, no_profile=False, overview=overview,
        )
    finally:
        db.close()


def _build_recommendation_overview(recs: list[dict]) -> dict:
    """Aggregate match-score stats and skill-gap insights across a user's recommendation set."""
    from collections import Counter

    scores = [r["match_percentage"] for r in recs]
    bands = {"90-100%": 0, "75-89%": 0, "60-74%": 0, "40-59%": 0, "Below 40%": 0}
    for s in scores:
        if s >= 90:
            bands["90-100%"] += 1
        elif s >= 75:
            bands["75-89%"] += 1
        elif s >= 60:
            bands["60-74%"] += 1
        elif s >= 40:
            bands["40-59%"] += 1
        else:
            bands["Below 40%"] += 1

    missing_counts = Counter()
    for r in recs:
        missing_counts.update(r.get("missing_skills") or [])

    return {
        "average": round(sum(scores) / len(scores), 1) if scores else 0.0,
        "highest": max(scores) if scores else 0.0,
        "lowest": min(scores) if scores else 0.0,
        "bands": bands,
        "max_band_count": max(bands.values()) if bands else 1,
        "top_missing_skills": missing_counts.most_common(8),
    }


@jobs_bp.route("/<job_id>")
@login_required
def job_detail(job_id):
    """Full job detail page with description, skills, match breakdown, and similar jobs."""
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id, Job.is_active.is_(True)).first()
        if not job:
            return "Job not found", 404

        skills = [s.skill for s in db.query(JobSkill).filter(JobSkill.job_id == job.id).all()]

        saved_ids = {
            str(s.job_id) for s in
            db.query(SavedJob).filter(SavedJob.user_id == current_user.id).all()
        }
        is_saved = str(job.id) in saved_ids

        similar_jobs = []
        if job.embedding is not None:
            from sqlalchemy import text
            stmt = text("""
                SELECT id, title, title_clean, company, location_city, location_country, remote, category,
                       (1 - (embedding <=> :embedding)) AS similarity
                FROM jobs
                WHERE id != :job_id AND embedding IS NOT NULL AND is_active = true
                ORDER BY embedding <=> :embedding
                LIMIT 5
            """)
            embedding_literal = "[" + ",".join(map(str, job.embedding)) + "]"
            rows = db.execute(stmt, {"embedding": embedding_literal, "job_id": job.id}).fetchall()
            similar_jobs = rows

        breakdown = None
        matching_skills = []
        missing_skills = []
        profile = current_user.profile
        if profile and (profile.skills or profile.headline):
            import numpy as np
            if profile.profile_embedding is not None and job.embedding is not None:
                a, b = np.array(profile.profile_embedding), np.array(job.embedding)
                denom = np.linalg.norm(a) * np.linalg.norm(b)
                similarity = float(np.dot(a, b) / denom) if denom else 0.0
            else:
                similarity = 0.0
            breakdown = compute_match_score(profile, job, skills, similarity, getattr(profile, 'preferred_job_types', None))
            matching_skills = breakdown.matching_skills
            missing_skills = breakdown.missing_skills

        return render_template(
            "main/job_detail.html",
            job=job, skills=skills, is_saved=is_saved,
            similar_jobs=similar_jobs, breakdown=breakdown,
            matching_skills=matching_skills, missing_skills=missing_skills,
        )
    finally:
        db.close()


@jobs_bp.route("/explain/<job_id>")
@login_required
def explain(job_id):
    """AJAX endpoint - generates an explanation for a single job on demand."""
    db = SessionLocal()
    try:
        profile = current_user.profile
        job = db.query(Job).filter(Job.id == job_id, Job.is_active.is_(True)).first()
        if not job or not profile:
            return jsonify({"error": "Not found"}), 404

        job_skills = [s.skill for s in db.query(JobSkill).filter(JobSkill.job_id == job.id).all()]

        import numpy as np
        if profile.profile_embedding is not None and job.embedding is not None:
            a, b = np.array(profile.profile_embedding), np.array(job.embedding)
            denom = np.linalg.norm(a) * np.linalg.norm(b)
            similarity = float(np.dot(a, b) / denom) if denom else 0.0
        else:
            similarity = 0.0

        breakdown = compute_match_score(profile, job, job_skills, similarity, getattr(profile, 'preferred_job_types', None))
        result = generate_explanation(profile, job, breakdown)

        response = {
            "explanation": result.to_text(),
            "headline": result.headline or None,
            "strengths": result.strengths or None,
            "gaps": result.gaps or None,
            "recommendation": result.recommendation or None,
            "confidence": result.confidence if result.confidence else None,
            "match_tier": result.match_tier,
        }
        if result.error:
            response["error"] = result.error
        return jsonify(response)
    finally:
        db.close()


@jobs_bp.route("/feed/new")
@login_required
def feed_new():
    """Return new jobs posted since a given timestamp, ranked by profile relevance.

    Uses the user's profile embedding for semantic similarity when available.
    Falls back to saved-job similarity, then chronological order.
    """
    from datetime import datetime
    from sqlalchemy import text

    since_str = request.args.get("since", "")
    limit = min(request.args.get("limit", 10, type=int), 20)

    db = SessionLocal()
    try:
        profile = db.query(UserProfile).filter(
            UserProfile.user_id == current_user.id
        ).first()

        saved_ids = {
            str(s.job_id) for s in
            db.query(SavedJob).filter(SavedJob.user_id == current_user.id).all()
        }

        # Base filter: new jobs since timestamp, active only
        time_filter = ""
        params = {"lim": limit * 3}
        if since_str:
            try:
                since = datetime.fromisoformat(since_str.replace("Z", "+00:00"))
                time_filter = "AND j.created_at > :since"
                params["since"] = since
            except ValueError:
                pass

        new_jobs = []

        # 1) Profile-based: find new jobs semantically similar to user's profile
        if profile and profile.profile_embedding is not None:
            try:
                stmt = text(f"""
                    SELECT j.id, j.title, j.title_clean, j.company,
                           j.location_city, j.location_country, j.remote,
                           j.salary_min, j.salary_max, j.salary_currency,
                           j.category, j.job_type, j.url, j.source, j.created_at,
                           (1 - (j.embedding <=> :profile_vec)) AS similarity
                    FROM jobs j
                    WHERE j.embedding IS NOT NULL
                      AND j.is_active = true
                      {time_filter}
                    ORDER BY j.embedding <=> :profile_vec
                    LIMIT :lim
                """)
                params["profile_vec"] = str(profile.profile_embedding)
                rows = db.execute(stmt, params).fetchall()
                new_jobs = rows
            except Exception:
                pass

        # 2) Saved-job similarity: find new jobs similar to user's saved jobs
        if not new_jobs and saved_ids:
            try:
                saved_uuids = [uuid.UUID(sid) for sid in saved_ids]
                params["saved_uuids"] = saved_uuids
                # Remove profile_vec if it was set
                params.pop("profile_vec", None)
                stmt = text(f"""
                    SELECT DISTINCT j.id, j.title, j.title_clean, j.company,
                           j.location_city, j.location_country, j.remote,
                           j.salary_min, j.salary_max, j.salary_currency,
                           j.category, j.job_type, j.url, j.source, j.created_at,
                           MAX(1 - (j.embedding <=> ref.embedding)) AS similarity
                    FROM jobs j
                    CROSS JOIN jobs ref
                    WHERE ref.id = ANY(SELECT unnest(:saved_uuids))
                      AND j.id != ref.id
                      AND j.embedding IS NOT NULL
                      AND ref.embedding IS NOT NULL
                      AND j.is_active = true
                      {time_filter}
                    GROUP BY j.id, j.title, j.title_clean, j.company,
                             j.location_city, j.location_country, j.remote,
                             j.salary_min, j.salary_max, j.salary_currency,
                             j.category, j.job_type, j.url, j.source, j.created_at
                    ORDER BY similarity DESC
                    LIMIT :lim
                """)
                rows = db.execute(stmt, params).fetchall()
                new_jobs = rows
            except Exception:
                pass

        # 3) Fallback: all new jobs (chronological)
        if not new_jobs:
            query = db.query(Job).filter(Job.is_active.is_(True))
            if since_str:
                try:
                    since = datetime.fromisoformat(since_str.replace("Z", "+00:00"))
                    query = query.filter(Job.created_at > since)
                except ValueError:
                    pass
            new_jobs = query.order_by(Job.created_at.desc()).limit(limit).all()

        results = []
        for job in new_jobs:
            # Handle both Row objects (from raw SQL) and Job model instances
            job_id = str(job.id) if hasattr(job, "id") else str(job[0])
            title = job.title_clean or job.title if hasattr(job, "title_clean") else (job[2] or job[1])
            company = job.company if hasattr(job, "company") else job[3]
            results.append({
                "id": job_id,
                "title": title,
                "company": company,
                "location_city": job.location_city if hasattr(job, "location_city") else job[4],
                "location_country": job.location_country if hasattr(job, "location_country") else job[5],
                "remote": job.remote if hasattr(job, "remote") else job[6],
                "salary_min": job.salary_min if hasattr(job, "salary_min") else job[7],
                "salary_max": job.salary_max if hasattr(job, "salary_max") else job[8],
                "salary_currency": job.salary_currency if hasattr(job, "salary_currency") else job[9],
                "category": job.category if hasattr(job, "category") else job[10],
                "job_type": job.job_type if hasattr(job, "job_type") else job[11],
                "url": job.url if hasattr(job, "url") else job[12],
                "source": job.source if hasattr(job, "source") else job[13],
                "is_saved": job_id in saved_ids,
            })

        newest_time = None
        if new_jobs:
            job0 = new_jobs[0]
            newest_time = (job0.created_at.isoformat() if hasattr(job0, "created_at")
                           else (job0[14].isoformat() if hasattr(job0[14], "isoformat") else str(job0[14])))
        if not newest_time:
            newest_time = since_str

        return jsonify({
            "jobs": results,
            "count": len(results),
            "newest_time": newest_time,
        })
    finally:
        db.close()


@jobs_bp.route("/save/<job_id>", methods=["POST"])
@login_required
def save(job_id):
    db = SessionLocal()
    try:
        existing = db.query(SavedJob).filter(
            SavedJob.user_id == current_user.id, SavedJob.job_id == job_id
        ).first()
        if existing:
            return jsonify({"saved": True})

        db.add(SavedJob(id=uuid.uuid4(), user_id=current_user.id, job_id=uuid.UUID(job_id)))
        db.commit()
        return jsonify({"saved": True})
    finally:
        db.close()


@jobs_bp.route("/unsave/<job_id>", methods=["POST"])
@login_required
def unsave(job_id):
    db = SessionLocal()
    try:
        existing = db.query(SavedJob).filter(
            SavedJob.user_id == current_user.id, SavedJob.job_id == job_id
        ).first()
        if existing:
            db.delete(existing)
            db.commit()
        return jsonify({"saved": False})
    finally:
        db.close()


@jobs_bp.route("/saved")
@login_required
def saved():
    db = SessionLocal()
    try:
        rows = (
            db.query(SavedJob, Job)
            .join(Job, Job.id == SavedJob.job_id)
            .filter(SavedJob.user_id == current_user.id, Job.is_active.is_(True))
            .order_by(SavedJob.saved_at.desc())
            .all()
        )
        return render_template("main/saved.html", rows=rows)
    finally:
        db.close()


@jobs_bp.route("/recent")
@login_required
def recent():
    db = SessionLocal()
    try:
        profile = db.query(UserProfile).filter(
            UserProfile.user_id == current_user.id
        ).first()

        if profile and profile.profile_embedding is not None:
            try:
                from sqlalchemy import text as sql_text
                stmt = sql_text("""
                    SELECT j.id, j.title, j.title_clean, j.company,
                           j.location_city, j.location_country, j.remote,
                           j.salary_min, j.salary_max, j.salary_currency,
                           j.category, j.job_type, j.url, j.source, j.created_at,
                           (1 - (j.embedding <=> :profile_vec)) AS similarity
                    FROM jobs j
                    WHERE j.embedding IS NOT NULL
                      AND j.is_active = true
                    ORDER BY j.created_at DESC, j.embedding <=> :profile_vec
                    LIMIT 30
                """)
                jobs = db.execute(stmt, {"profile_vec": str(profile.profile_embedding)}).fetchall()
            except Exception:
                jobs = db.query(Job).filter(Job.is_active.is_(True)).order_by(Job.created_at.desc()).limit(30).all()
        else:
            jobs = db.query(Job).filter(Job.is_active.is_(True)).order_by(Job.created_at.desc()).limit(30).all()

        saved_ids = {
            str(s.job_id) for s in
            db.query(SavedJob).filter(SavedJob.user_id == current_user.id).all()
        }
        return render_template("main/recent.html", jobs=jobs, saved_ids=saved_ids)
    finally:
        db.close()
