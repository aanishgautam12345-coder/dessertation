"""Trigger instant email notifications after new recommendations are generated.

Runs notification delivery in a background thread so the API response is not
blocked by SMTP latency. Notification failures are logged but never crash
the recommendation flow.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, Future
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal
from app.models.user import NotificationPreference, User

logger = logging.getLogger(__name__)

_executor: ThreadPoolExecutor | None = None


def _get_executor() -> ThreadPoolExecutor:
    """Lazy-init a small thread pool for background notification sends."""
    global _executor
    if _executor is None:
        _executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="notif")
    return _executor


def _trigger_notifications(user_id: int) -> None:
    """Send pending notifications for a single user. Runs in a background thread."""
    db: Session | None = None
    try:
        db = SessionLocal()
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning("Notification trigger: user %s not found", user_id)
            return

        prefs = db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id
        ).first()
        if not prefs or not prefs.email_enabled:
            logger.debug("Notification trigger: user %s has notifications disabled", user_id)
            return

        from app.agents.notification_agent import NotificationAgent
        agent = NotificationAgent(db)
        result = agent.check_recommendation_updates(user)
        logger.info("Notification trigger: user %s delivered=%s", user_id, result)
    except Exception:
        logger.exception("Notification trigger failed for user %s", user_id)
    finally:
        if db is not None:
            db.close()


def dispatch_notification_async(user_id: int) -> None:
    """Submit a notification check to the background thread pool.

    This is fire-and-forget: the caller does not wait for completion.
    """
    settings = get_settings()
    if not settings.smtp_user or not settings.smtp_password:
        return

    executor = _get_executor()
    future: Future = executor.submit(_trigger_notifications, user_id)
    future.add_done_callback(
        lambda f: logger.debug(
            "Notification dispatch complete user=%s ok=%s",
            user_id,
            f.exception() is None,
        ) if f.exception() is None else None
    )


def shutdown_executor() -> None:
    """Shutdown the thread pool gracefully (call on app shutdown)."""
    global _executor
    if _executor is not None:
        _executor.shutdown(wait=False)
        _executor = None
