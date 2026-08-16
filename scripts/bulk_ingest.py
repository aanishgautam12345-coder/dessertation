"""Bulk ingestion: CSV datasets + API sources + processing pipeline.

Runs the full ingestion pipeline in sequence:
  1. Seed remaining rows from job_skill_set.csv (csv)
  2. Seed 50K rows from job_descriptions2.csv (csv2)
  3. Seed fresh UK jobs from Adzuna API
  4. Seed fresh UK jobs from Reed API
  5. Process all unprocessed raw_jobs through the pipeline

Usage:
    python -m scripts.bulk_ingest                    # full run
    python -m scripts.bulk_ingest --skip-apis        # skip Adzuna/Reed
    python -m scripts.bulk_ingest --csv2-limit 10000 # custom csv2 limit
    python -m scripts.bulk_ingest --process-only     # only run processing pipeline
"""

import sys
import os
import time
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.dialects.postgresql import insert
from app.database import SessionLocal, init_db
from app.models import *  # noqa: F401,F403
from app.models.job import RawJob


def _count_unprocessed():
    db = SessionLocal()
    try:
        return db.query(RawJob).filter(RawJob.processed == False).count()
    finally:
        db.close()


def seed_csv(limit=None):
    """Seed remaining rows from job_skill_set.csv."""
    print("\n--- [1/5] Seeding job_skill_set.csv ---")
    from app.ingestion.csv_source import CsvSource

    file_path = "data/job_skill_set.csv"
    source = CsvSource(file_path, limit=limit)
    records = source.fetch()

    db = SessionLocal()
    inserted = 0
    skipped = 0
    try:
        for record in records:
            stmt = insert(RawJob).values(
                source=record.source,
                source_job_id=record.source_job_id,
                payload=record.payload,
                processed=False,
            ).on_conflict_do_nothing(index_elements=["source", "source_job_id"])
            result = db.execute(stmt)
            if result.rowcount > 0:
                inserted += 1
            else:
                skipped += 1
        db.commit()
        print(f"  Inserted: {inserted:,} | Skipped (dupes): {skipped:,}")
    finally:
        db.close()
    return inserted


def seed_csv2(limit=50000):
    """Seed rows from job_descriptions2.csv."""
    print(f"\n--- [2/5] Seeding job_descriptions2.csv (limit: {limit:,}) ---")
    from app.ingestion.csv_descriptions2 import CsvDescriptions2Source

    file_path = "data/job_descriptions2.csv"
    source = CsvDescriptions2Source(file_path, limit=limit)
    records = source.fetch()

    db = SessionLocal()
    inserted = 0
    skipped = 0
    try:
        for record in records:
            stmt = insert(RawJob).values(
                source=record.source,
                source_job_id=record.source_job_id,
                payload=record.payload,
                processed=False,
            ).on_conflict_do_nothing(index_elements=["source", "source_job_id"])
            result = db.execute(stmt)
            if result.rowcount > 0:
                inserted += 1
            else:
                skipped += 1
        db.commit()
        print(f"  Inserted: {inserted:,} | Skipped (dupes): {skipped:,}")
    finally:
        db.close()
    return inserted


def seed_adzuna(keywords="python", country="gb", max_pages=3):
    """Seed fresh UK jobs from Adzuna API."""
    print(f"\n--- [3/5] Seeding Adzuna ({country}, keywords={keywords}) ---")
    from app.ingestion.adzuna_source import AdzunaSource

    try:
        source = AdzunaSource(keywords=keywords, country=country, max_pages=max_pages)
        records = source.fetch()
    except Exception as e:
        print(f"  Skipped: {e}")
        return 0

    db = SessionLocal()
    inserted = 0
    skipped = 0
    try:
        for record in records:
            stmt = insert(RawJob).values(
                source=record.source,
                source_job_id=record.source_job_id,
                payload=record.payload,
                processed=False,
            ).on_conflict_do_nothing(index_elements=["source", "source_job_id"])
            result = db.execute(stmt)
            if result.rowcount > 0:
                inserted += 1
            else:
                skipped += 1
        db.commit()
        print(f"  Inserted: {inserted:,} | Skipped (dupes): {skipped:,}")
    finally:
        db.close()
    return inserted


def seed_reed(keywords="python", location="london", max_pages=5):
    """Seed fresh UK jobs from Reed API."""
    print(f"\n--- [4/5] Seeding Reed (keywords={keywords}, location={location}) ---")
    from app.ingestion.reed_source import ReedSource

    try:
        source = ReedSource(keywords=keywords, location=location, max_pages=max_pages)
        records = source.fetch()
    except Exception as e:
        print(f"  Skipped: {e}")
        return 0

    db = SessionLocal()
    inserted = 0
    skipped = 0
    try:
        for record in records:
            stmt = insert(RawJob).values(
                source=record.source,
                source_job_id=record.source_job_id,
                payload=record.payload,
                processed=False,
            ).on_conflict_do_nothing(index_elements=["source", "source_job_id"])
            result = db.execute(stmt)
            if result.rowcount > 0:
                inserted += 1
            else:
                skipped += 1
        db.commit()
        print(f"  Inserted: {inserted:,} | Skipped (dupes): {skipped:,}")
    finally:
        db.close()
    return inserted


def process_all(limit=None, generate_embeddings=True):
    """Process all unprocessed raw_jobs through the pipeline."""
    unprocessed = _count_unprocessed()
    print(f"\n--- [5/5] Processing pipeline ---")
    print(f"  Unprocessed raw_jobs: {unprocessed:,}")
    if unprocessed == 0:
        print("  Nothing to process.")
        return

    from app.processing.pipeline import process_raw_jobs

    db = SessionLocal()
    try:
        start = time.time()
        process_raw_jobs(
            db=db,
            limit=limit,
            generate_embeddings=generate_embeddings,
        )
        elapsed = time.time() - start
        print(f"  Processing completed in {elapsed:.1f}s")
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Bulk ingestion pipeline")
    parser.add_argument("--csv-limit", type=int, default=None,
                        help="Max rows from job_skill_set.csv (None = all remaining)")
    parser.add_argument("--csv2-limit", type=int, default=50000,
                        help="Max rows from job_descriptions2.csv")
    parser.add_argument("--skip-apis", action="store_true",
                        help="Skip Adzuna and Reed API calls")
    parser.add_argument("--process-only", action="store_true",
                        help="Only run the processing pipeline (skip seeding)")
    parser.add_argument("--no-embeddings", action="store_true",
                        help="Skip embedding generation during processing")
    parser.add_argument("--adzuna-keywords", default="python",
                        help="Keywords for Adzuna search")
    parser.add_argument("--reed-keywords", default="python",
                        help="Keywords for Reed search")
    args = parser.parse_args()

    init_db()

    total_start = time.time()
    print("=" * 60)
    print("  JobMatch - Bulk Ingestion Pipeline")
    print("=" * 60)

    before = _count_unprocessed()
    print(f"\n  Starting unprocessed raw_jobs: {before:,}")

    if not args.process_only:
        seed_csv(limit=args.csv_limit)
        seed_csv2(limit=args.csv2_limit)

        if not args.skip_apis:
            # Ingest from multiple keyword queries for variety
            for kw in ["python", "javascript", "data engineer", "devops"]:
                seed_adzuna(keywords=kw, country="gb", max_pages=2)
            for kw in ["python", "javascript", "data engineer", "devops"]:
                seed_reed(keywords=kw, location="london", max_pages=2)
        else:
            print("\n--- [3/5] Skipped Adzuna (--skip-apis) ---")
            print("--- [4/5] Skipped Reed (--skip-apis) ---")

    after_seed = _count_unprocessed()
    print(f"\n  Raw jobs to process: {after_seed:,} (was {before:,})")

    process_all(
        limit=None,
        generate_embeddings=not args.no_embeddings,
    )

    total_elapsed = time.time() - total_start
    print("\n" + "=" * 60)
    print(f"  Total time: {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")
    print("=" * 60)

    # Final counts
    db = SessionLocal()
    try:
        from app.models.job import Job
        from sqlalchemy import func
        raw = db.query(func.count(RawJob.id)).scalar()
        jobs = db.query(func.count(Job.id)).scalar()
        active = db.query(func.count(Job.id)).filter(Job.is_active == True).scalar()
        embedded = db.query(func.count(Job.id)).filter(Job.embedding.isnot(None)).scalar()
        print(f"\n  Final state:")
        print(f"    Raw jobs:     {raw:>8,}")
        print(f"    Canonical:    {jobs:>8,}")
        print(f"    Active:       {active:>8,}")
        print(f"    With embed:   {embedded:>8,}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
