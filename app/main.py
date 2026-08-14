"""JobMatch - FastAPI Application Entry Point.

Start the server:
    uvicorn app.main:app --reload
"""

import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.database import init_db

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Rate limiter - in-memory store (suitable for single-process dev)
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="JobMatch",
    description="Job Vacancy Aggregator and Personalised Recommendation System",
    version="0.1.0",
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5000",   # Flask frontend
        "http://127.0.0.1:5000",
        "http://localhost:8000",   # FastAPI itself (for API docs)
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()
    logger.info("JobMatch started")

    # Start notification scheduler if enabled
    from app.config import get_settings
    settings = get_settings()
    if settings.scheduler_enabled:
        from app.services.scheduler import start_scheduler
        start_scheduler()
        logger.info("Notification scheduler enabled")

    # Start ingestion scheduler if enabled
    if settings.scheduler_enabled:
        from app.services.ingestion_scheduler import start_ingestion_scheduler
        start_ingestion_scheduler()
        logger.info("Ingestion scheduler enabled")


@app.on_event("shutdown")
def on_shutdown():
    from app.services.notification_trigger import shutdown_executor
    from app.services.ingestion_scheduler import stop_ingestion_scheduler
    shutdown_executor()
    stop_ingestion_scheduler()
    logger.info("JobMatch shut down")


@app.get("/health")
@limiter.exempt
def health_check():
    return {"status": "ok", "service": "JobMatch"}


# Route registration
from app.api import jobs, auth, users, jobs_extended, admin
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(jobs_extended.router, prefix="/api/jobs", tags=["Jobs Extended"])
app.include_router(admin.router, prefix="/api/admin", tags=["Administration"])

from app.api import recommendations
from app.api import interactions
from app.api import notifications
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["Recommendations"])
app.include_router(interactions.router, prefix="/api", tags=["Interactions"])
app.include_router(notifications.router, prefix="/api", tags=["Notifications"])
