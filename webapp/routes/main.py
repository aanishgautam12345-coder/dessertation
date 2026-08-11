"""Main Routes - landing page and home dashboard."""

import uuid

from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.job import Job
from app.models.user import UserProfile
from app.models.recommendation import SavedJob

main_bp = Blueprint("main", __name__)


def _profile_feed(db: Session, profile: UserProfile, limit: int = 20) -> list:
    """Find jobs semantically similar to the user's profile embedding."""
    if profile.profile_embedding is None:
        return []

    try:
        stmt = text("""
            SELECT j.id, j.title, j.title_clean, j.company,
                   j.location_city, j.location_country, j.remote,
                   j.salary_min, j.salary_max, j.salary_currency,
                   j.category, j.job_type, j.url, j.source, j.created_at,
                   (1 - (j.embedding <=> :profile_vec)) AS similarity
            FROM jobs j
            WHERE j.embedding IS NOT NULL
              AND j.is_active = true
            ORDER BY j.embedding <=> :profile_vec
            LIMIT :lim
        """)
        rows = db.execute(stmt, {
            "profile_vec": str(profile.profile_embedding),
            "lim": limit,
        }).fetchall()
        return rows
    except Exception:
        return []


def _saved_feed(db: Session, user_id, limit: int = 20) -> list:
    """Find jobs similar to the user's saved jobs via embedding."""
    saved_uuids = [
        uuid.UUID(str(s.job_id))
        for s in db.query(SavedJob).filter(SavedJob.user_id == user_id).all()
    ]
    if not saved_uuids:
        return []

    try:
        stmt = text("""
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
              AND j.id NOT IN (SELECT unnest(:saved_uuids))
            GROUP BY j.id, j.title, j.title_clean, j.company,
                     j.location_city, j.location_country, j.remote,
                     j.salary_min, j.salary_max, j.salary_currency,
                     j.category, j.job_type, j.url, j.source, j.created_at
            ORDER BY similarity DESC
            LIMIT :lim
        """)
        rows = db.execute(stmt, {"saved_uuids": saved_uuids, "lim": limit}).fetchall()
        return rows
    except Exception:
        return []


def _recent_feed(db: Session, limit: int = 15, profile: UserProfile | None = None) -> list:
    """Most recent active jobs, ranked by profile similarity when available."""
    if profile and profile.profile_embedding is not None:
        try:
            stmt = text("""
                SELECT j.id, j.title, j.title_clean, j.company,
                       j.location_city, j.location_country, j.remote,
                       j.salary_min, j.salary_max, j.salary_currency,
                       j.category, j.job_type, j.url, j.source, j.created_at,
                       (1 - (j.embedding <=> :profile_vec)) AS similarity
                FROM jobs j
                WHERE j.embedding IS NOT NULL
                  AND j.is_active = true
                ORDER BY j.created_at DESC, j.embedding <=> :profile_vec
                LIMIT :lim
            """)
            rows = db.execute(stmt, {
                "profile_vec": str(profile.profile_embedding),
                "lim": limit,
            }).fetchall()
            if rows:
                return rows
        except Exception:
            pass

    return db.query(Job).order_by(Job.created_at.desc()).limit(limit).all()


def _merge_feeds(*feeds: list) -> list:
    """Merge multiple feeds, deduplicating by job.id and keeping highest similarity."""
    seen: dict[str, int] = {}  # job_id -> index in merged
    merged = []

    for feed in feeds:
        for row in feed:
            job_id = str(row.id) if hasattr(row, "id") else str(row[0])
            if job_id in seen:
                continue
            seen[job_id] = len(merged)
            merged.append(row)

    return merged


@main_bp.route("/")
def index():
    if not current_user.is_authenticated:
        return render_template("landing.html")

    db = SessionLocal()
    try:
        total_jobs = db.query(Job).count()
        categories = (
            db.query(Job.category, func.count(Job.id))
            .group_by(Job.category)
            .order_by(func.count(Job.id).desc())
            .limit(5)
            .all()
        )

        saved_ids = {
            str(s.job_id) for s in
            db.query(SavedJob).filter(SavedJob.user_id == current_user.id).all()
        }

        profile = db.query(UserProfile).filter(
            UserProfile.user_id == current_user.id
        ).first()

        # Build feed: profile-based > saved-based > recent
        feed_jobs = []
        feed_source = "recent"

        # 1) Profile-based feed (highest priority)
        if profile:
            profile_jobs = _profile_feed(db, profile, limit=20)
            if profile_jobs:
                feed_jobs = profile_jobs
                feed_source = "profile"

        # 2) Saved-job similarity (supplements or replaces empty profile feed)
        if not feed_jobs:
            saved_jobs = _saved_feed(db, current_user.id, limit=20)
            if saved_jobs:
                feed_jobs = saved_jobs
                feed_source = "saved"

        # 3) Recent jobs (fallback)
        if not feed_jobs:
            feed_jobs = _recent_feed(db, limit=15, profile=profile)
            feed_source = "recent"

        return render_template(
            "main/home.html",
            total_jobs=total_jobs,
            categories=categories,
            feed_jobs=feed_jobs,
            feed_source=feed_source,
            saved_ids=saved_ids,
        )
    finally:
        db.close()
