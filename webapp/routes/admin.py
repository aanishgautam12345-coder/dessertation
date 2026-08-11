"""Administrator browser interface."""

import uuid

from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy import or_

from app.database import SessionLocal
from app.models.ingestion_run import IngestionRun
from app.models.job import Job
from app.models.normalization_alias import NormalizationAlias
from app.models.processing_error import ProcessingError
from app.processing.category import CATEGORIES
from app.services.admin import (
    AdminValidationError,
    preview_normalization,
    reprocess_raw_jobs,
    sanitize_error,
    save_alias,
    update_job,
)
from webapp.routes.admin_guard import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
PAGE_SIZE = 25


@admin_bp.route("/")
@admin_required
def index():
    return redirect(url_for("admin.ingestion_runs"))


@admin_bp.route("/ingestion-runs")
@admin_required
def ingestion_runs():
    db = SessionLocal()
    try:
        page = max(request.args.get("page", 1, type=int), 1)
        query = db.query(IngestionRun)
        source = request.args.get("source", "").strip()
        status = request.args.get("status", "").strip()
        if source:
            query = query.filter(IngestionRun.source == source)
        if status:
            query = query.filter(IngestionRun.status == status)
        total = query.count()
        runs = query.order_by(IngestionRun.started_at.desc()).offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE).all()
        return render_template(
            "admin/ingestion_runs.html", runs=runs, page=page, total=total,
            page_size=PAGE_SIZE, source=source, status=status, sanitize_error=sanitize_error,
        )
    finally:
        db.close()


@admin_bp.route("/ingestion-runs/<uuid:run_id>")
@admin_required
def ingestion_run_detail(run_id):
    db = SessionLocal()
    try:
        run = db.get(IngestionRun, run_id)
        if not run:
            return "Ingestion run not found", 404
        errors = db.query(ProcessingError).filter(ProcessingError.ingestion_run_id == run.id).all()
        return render_template(
            "admin/ingestion_run_detail.html", run=run, errors=errors,
            sanitize_error=sanitize_error,
        )
    finally:
        db.close()


@admin_bp.route("/reprocess", methods=["GET", "POST"])
@admin_required
def reprocess():
    if request.method == "POST":
        if request.form.get("confirmed") != "yes":
            flash("Confirm the bounded reprocessing request.", "error")
            return redirect(url_for("admin.reprocess"))
        db = SessionLocal()
        try:
            raw_id = request.form.get("raw_job_id", "").strip()
            summary = reprocess_raw_jobs(
                db,
                raw_job_id=uuid.UUID(raw_id) if raw_id else None,
                ingestion_run_id=(
                    uuid.UUID(request.form["ingestion_run_id"])
                    if request.form.get("ingestion_run_id", "").strip() else None
                ),
                source=request.form.get("source", "").strip() or None,
                failed_only=request.form.get("failed_only") == "on",
                limit=request.form.get("limit", 100, type=int),
            )
            flash(
                f"Reprocessing complete: {summary['inserted']} inserted, "
                f"{summary['skipped']} skipped, {summary['errors']} failed.",
                "success",
            )
        except (AdminValidationError, ValueError) as exc:
            db.rollback()
            flash(str(exc), "error")
        finally:
            db.close()
        return redirect(url_for("admin.reprocess"))
    return render_template("admin/reprocess.html")


@admin_bp.route("/jobs")
@admin_required
def jobs():
    db = SessionLocal()
    try:
        page = max(request.args.get("page", 1, type=int), 1)
        q = request.args.get("q", "").strip()
        source = request.args.get("source", "").strip()
        category = request.args.get("category", "").strip()
        status = request.args.get("status", "").strip()
        min_quality = request.args.get("min_quality", type=float)
        query = db.query(Job)
        if q:
            query = query.filter(or_(Job.title.ilike(f"%{q}%"), Job.company.ilike(f"%{q}%")))
        if source:
            query = query.filter(Job.source == source)
        if category:
            query = query.filter(Job.category == category)
        if status in {"active", "archived"}:
            query = query.filter(Job.is_active.is_(status == "active"))
        if min_quality is not None:
            query = query.filter(Job.quality_score >= min_quality)
        total = query.count()
        rows = query.order_by(Job.created_at.desc()).offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE).all()
        return render_template(
            "admin/jobs.html", jobs=rows, page=page, total=total, page_size=PAGE_SIZE,
            q=q, source=source, category=category, status=status, categories=CATEGORIES,
            min_quality=min_quality,
        )
    finally:
        db.close()


@admin_bp.route("/jobs/create", methods=["GET", "POST"])
@admin_required
def job_create():
    if request.method == "POST":
        db = SessionLocal()
        try:
            from app.processing.title import clean_title
            from app.processing.quality import score_job
            from app.processing.dedup import generate_dedup_hash
            from app.services.embedding import generate_embedding, build_job_text
            from app.models.job import JobSkill
            import uuid

            title = request.form.get("title", "").strip()
            if not title:
                flash("Title is required.", "error")
                return redirect(url_for("admin.job_create"))

            company = request.form.get("company", "").strip() or None
            description = request.form.get("description", "").strip() or None
            requirements = request.form.get("requirements", "").strip() or None
            responsibilities = request.form.get("responsibilities", "").strip() or None
            location_city = request.form.get("location_city", "").strip() or None
            location_country = request.form.get("location_country", "").strip() or None
            remote = request.form.get("remote") == "on"
            category = request.form.get("category", "").strip() or None
            job_type = request.form.get("job_type", "").strip() or None
            experience_level = request.form.get("experience_level", "").strip() or None
            salary_min = request.form.get("salary_min", type=float)
            salary_max = request.form.get("salary_max", type=float)
            salary_currency = request.form.get("salary_currency", "").strip() or None
            salary_period = request.form.get("salary_period", "").strip() or None
            url_val = request.form.get("url", "").strip() or None
            skills_raw = request.form.get("skills", "").strip()
            skills_list = [s.strip() for s in skills_raw.split(",") if s.strip()] if skills_raw else []

            title_clean = clean_title(title)
            dedup_hash = generate_dedup_hash(
                title_clean, company,
                f"{location_city or ''} {location_country or ''}".strip(),
                salary_min, salary_max,
            )

            existing = db.query(Job).filter(Job.dedup_hash == dedup_hash).first()
            if existing:
                flash("A job with identical title, company, location, and salary already exists.", "error")
                return redirect(url_for("admin.job_create"))

            text_for_embedding = build_job_text(
                title_clean, description or "", skills_list or None,
                location_city=location_city, location_country=location_country,
                remote=remote,
            )
            embedding = generate_embedding(text_for_embedding)

            quality = score_job(
                title=title_clean, company=company, description=description,
                location_city=location_city, location_country=location_country,
                salary_min=salary_min, salary_max=salary_max,
                category=category, job_type=job_type,
                experience_level=experience_level, skills=skills_list or None,
                url=url_val, source="admin",
            )

            new_job = Job(
                id=uuid.uuid4(),
                title=title,
                title_clean=title_clean,
                company=company,
                description=description,
                requirements=requirements,
                responsibilities=responsibilities,
                location_city=location_city,
                location_country=location_country,
                remote=remote,
                category=category,
                job_type=job_type,
                experience_level=experience_level,
                salary_min=salary_min,
                salary_max=salary_max,
                salary_currency=salary_currency,
                salary_period=salary_period,
                url=url_val,
                source="admin",
                dedup_hash=dedup_hash,
                embedding=embedding,
                quality_score=quality.overall,
                processing_version="2.0",
                is_active=True,
            )
            db.add(new_job)
            db.flush()

            for skill_name in skills_list:
                db.add(JobSkill(id=uuid.uuid4(), job_id=new_job.id, skill=skill_name))

            db.commit()
            flash(f"Job created (quality score: {quality.overall:.0f}).", "success")
            return redirect(url_for("admin.job_detail", job_id=new_job.id))
        except Exception as exc:
            db.rollback()
            flash(f"Error creating job: {exc}", "error")
            return redirect(url_for("admin.job_create"))
        finally:
            db.close()
    return render_template("admin/job_create.html", categories=CATEGORIES)


@admin_bp.route("/jobs/<uuid:job_id>", methods=["GET", "POST"])
@admin_required
def job_detail(job_id):
    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        if not job:
            return "Job not found", 404
        if request.method == "POST":
            values = {key: request.form.get(key) for key in (
                "title_clean", "company", "description", "location_city", "location_country",
                "category", "job_type", "salary_min", "salary_max", "salary_currency",
                "salary_period", "url",
            )}
            values["remote"] = request.form.get("remote") == "on"
            try:
                update_job(db, job, values)
                flash("Job updated.", "success")
                return redirect(url_for("admin.job_detail", job_id=job.id))
            except AdminValidationError as exc:
                db.rollback()
                flash(str(exc), "error")
        return render_template("admin/job_detail.html", job=job, categories=CATEGORIES)
    finally:
        db.close()


@admin_bp.route("/jobs/<uuid:job_id>/status", methods=["POST"])
@admin_required
def job_status(job_id):
    if request.form.get("confirmed") != "yes":
        flash("Confirmation is required.", "error")
        return redirect(url_for("admin.job_detail", job_id=job_id))
    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        if not job:
            return "Job not found", 404
        job.is_active = request.form.get("active") == "true"
        db.commit()
        flash("Job restored." if job.is_active else "Job archived.", "success")
    finally:
        db.close()
    return redirect(url_for("admin.job_detail", job_id=job_id))


@admin_bp.route("/aliases", methods=["GET", "POST"])
@admin_required
def aliases():
    db = SessionLocal()
    try:
        if request.method == "POST":
            try:
                save_alias(
                    db, request.form.get("kind", ""), request.form.get("alias", ""),
                    request.form.get("canonical_value", ""),
                    is_active=request.form.get("is_active") == "on",
                )
                flash("Normalization alias saved.", "success")
                return redirect(url_for("admin.aliases"))
            except AdminValidationError as exc:
                db.rollback()
                flash(str(exc), "error")
        preview = None
        if request.args.get("preview_kind") and request.args.get("preview_value"):
            preview = preview_normalization(
                db, request.args["preview_kind"], request.args["preview_value"]
            )
        rows = db.query(NormalizationAlias).order_by(
            NormalizationAlias.kind, NormalizationAlias.alias
        ).all()
        return render_template("admin/aliases.html", aliases=rows, categories=CATEGORIES, preview=preview)
    finally:
        db.close()


@admin_bp.route("/aliases/<uuid:alias_id>/status", methods=["POST"])
@admin_required
def alias_status(alias_id):
    db = SessionLocal()
    try:
        mapping = db.get(NormalizationAlias, alias_id)
        if not mapping:
            return "Alias not found", 404
        mapping.is_active = request.form.get("active") == "true"
        db.commit()
        flash("Alias status updated.", "success")
    finally:
        db.close()
    return redirect(url_for("admin.aliases"))
