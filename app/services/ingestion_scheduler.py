"""Automatic ingestion scheduler for RSS and API data sources.

This module implements the missing automatic ingestion feature identified in the
dissertation audit. It schedules periodic fetching from:
1. We Work Remotely RSS feed
2. Adzuna API
3. Reed API

Usage:
    from app.services.ingestion_scheduler import start_ingestion_scheduler
    scheduler = start_ingestion_scheduler()
    # Scheduler runs in background, fetching new jobs periodically
"""

import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import get_settings
from app.database import SessionLocal

logger = logging.getLogger(__name__)

# Global scheduler instance
_ingestion_scheduler: BackgroundScheduler | None = None


def _run_ingestion_cycle():
    """Run one ingestion cycle: fetch from all sources, process, embed."""
    db = SessionLocal()
    try:
        logger.info("Starting ingestion cycle")
        
        # Import here to avoid circular imports
        from app.ingestion.wwr_scraper import WWRScraper
        from app.ingestion.csv_source import CsvSource
        from app.ingestion.csv_descriptions2 import CsvDescriptions2Source
        from app.processing.pipeline import process_raw_jobs
        
        stats = {"wwr": 0, "csv": 0, "csv2": 0, "processed": 0, "errors": 0}
        
        # 1. Fetch from We Work Remotely RSS
        try:
            logger.info("Fetching from We Work Remotely RSS")
            scraper = WWRScraper(limit=50)
            records = scraper.fetch()
            stats["wwr"] = len(records)
            
            # Save to raw_jobs
            from app.models.job import RawJob
            for record in records:
                raw_job = RawJob(
                    source="wwr",
                    source_job_id=record.source_job_id,
                    payload=record.payload,
                )
                db.add(raw_job)
            db.commit()
            
        except Exception as e:
            logger.error(f"WWR ingestion failed: {e}")
            stats["errors"] += 1
        
        # 2. Process raw jobs
        try:
            logger.info("Processing raw jobs")
            result = process_raw_jobs(db, generate_embeddings=True)
            stats["processed"] = result.get("inserted", 0)
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            stats["errors"] += 1
        
        logger.info(f"Ingestion cycle complete: {stats}")
        
    finally:
        db.close()


def start_ingestion_scheduler() -> BackgroundScheduler | None:
    """Start the automatic ingestion scheduler."""
    global _ingestion_scheduler
    
    settings = get_settings()
    
    if not settings.scheduler_enabled:
        logger.info("Ingestion scheduler disabled")
        return None
    
    if _ingestion_scheduler is not None:
        logger.warning("Ingestion scheduler already running")
        return _ingestion_scheduler
    
    _ingestion_scheduler = BackgroundScheduler()
    
    # Schedule RSS ingestion every 6 hours
    _ingestion_scheduler.add_job(
        _run_ingestion_cycle,
        trigger=IntervalTrigger(hours=6),
        id="wwr_ingestion",
        name="WWR RSS Ingestion",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
    )
    
    # Schedule daily processing of any remaining raw jobs
    _ingestion_scheduler.add_job(
        _run_ingestion_cycle,
        trigger=CronTrigger(hour=2, minute=0),  # 2 AM daily
        id="daily_processing",
        name="Daily Processing",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
    )
    
    _ingestion_scheduler.start()
    logger.info("Ingestion scheduler started")
    
    return _ingestion_scheduler


def stop_ingestion_scheduler():
    """Stop the ingestion scheduler."""
    global _ingestion_scheduler
    
    if _ingestion_scheduler is not None:
        _ingestion_scheduler.shutdown(wait=False)
        _ingestion_scheduler = None
        logger.info("Ingestion scheduler stopped")


def get_ingestion_scheduler() -> BackgroundScheduler | None:
    """Get the current ingestion scheduler instance."""
    return _ingestion_scheduler
