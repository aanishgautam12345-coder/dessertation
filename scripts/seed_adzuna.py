"""Seed the database from the Adzuna API.

Usage:
    python -m scripts.seed_adzuna --country gb --keywords "python developer" --maxPages 2
    python -m scripts.seed_adzuna --country gb --limit 100

Processing (raw_jobs -> jobs) runs separately via run_processing.
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.dialects.postgresql import insert
from app.database import SessionLocal, init_db
from app.models import *  # noqa: F401,F403
from app.models.job import RawJob
from app.ingestion.adzuna_source import AdzunaSource


def seed(
    country: str = "gb",
    keywords: str = "",
    results_per_page: int = 50,
    max_pages: int = 3,
    limit: int | None = None,
):
    # Ensure tables exist
    init_db()

    source = AdzunaSource(
        country=country,
        keywords=keywords,
        results_per_page=results_per_page,
        max_pages=max_pages,
    )
    records = source.fetch()

    if limit:
        records = records[:limit]

    # Write to raw_jobs, skip duplicates
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
            ).on_conflict_do_nothing(
                index_elements=["source", "source_job_id"]
            )
            result = db.execute(stmt)
            if result.rowcount > 0:
                inserted += 1
            else:
                skipped += 1

        db.commit()
        print(f"\nSeed complete: {inserted} inserted, {skipped} skipped (duplicates).")
        print(f"  Total raw_jobs in DB: {db.query(RawJob).count()}")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed raw_jobs from the Adzuna API")
    parser.add_argument("--country", default="gb", help="Country code (gb, us, au, ca, de, fr, in, nl)")
    parser.add_argument("--keywords", default="", help="Search keywords")
    parser.add_argument("--resultsPerPage", type=int, default=50, help="Results per page (max 50)")
    parser.add_argument("--maxPages", type=int, default=3, help="Max pages to fetch")
    parser.add_argument("--limit", type=int, default=None, help="Max jobs to import")
    args = parser.parse_args()

    seed(
        country=args.country,
        keywords=args.keywords,
        results_per_page=args.resultsPerPage,
        max_pages=args.maxPages,
        limit=args.limit,
    )
