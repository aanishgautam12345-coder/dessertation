"""Seed the database from the We Work Remotely RSS feed.

Usage:
    python -m scripts.seed_wwr
    python -m scripts.seed_wwr --limit 50

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
from app.ingestion.wwr_scraper import WWRScraper


def seed(limit: int = 100):
    # Ensure tables exist
    init_db()

    source = WWRScraper(limit=limit)
    records = source.fetch()

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
    parser = argparse.ArgumentParser(description="Seed raw_jobs from We Work Remotely RSS")
    parser.add_argument("--limit", type=int, default=100, help="Max jobs to import")
    args = parser.parse_args()

    seed(limit=args.limit)
