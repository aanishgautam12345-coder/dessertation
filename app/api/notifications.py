"""Notifications API - view notification history and statistics.

Endpoints:
    GET  /me/notifications     - paginated notification history
    GET  /me/notifications/stats - delivery statistics
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.notification import Notification
from app.models.user import User
from app.core.deps import get_current_user

router = APIRouter()


class NotificationItem(BaseModel):
    id: str
    job_id: str
    type: str
    match_score: float
    status: str
    sent_at: str | None
    created_at: str
    opened: bool


class NotificationListResponse(BaseModel):
    count: int
    results: list[NotificationItem]


class NotificationStatsResponse(BaseModel):
    total: int
    sent: int
    failed: int
    pending: int


@router.get("/me/notifications", response_model=NotificationListResponse)
def list_notifications(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get paginated notification history for the current user."""
    query = (
        db.query(Notification)
        .filter(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    items = query.all()

    return NotificationListResponse(
        count=db.query(func.count(Notification.id)).filter(
            Notification.user_id == user.id
        ).scalar(),
        results=[
            NotificationItem(
                id=str(n.id),
                job_id=str(n.job_id),
                type=n.type,
                match_score=n.match_score,
                status=n.status,
                sent_at=n.sent_at.isoformat() if n.sent_at else None,
                created_at=n.created_at.isoformat(),
                opened=n.opened,
            )
            for n in items
        ],
    )


@router.get("/me/notifications/stats", response_model=NotificationStatsResponse)
def notification_stats(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get notification delivery statistics for the current user."""
    base = db.query(func.count(Notification.id)).filter(Notification.user_id == user.id)
    total = base.scalar()
    sent = base.filter(Notification.status == "sent").scalar()
    failed = base.filter(Notification.status == "failed").scalar()
    pending = base.filter(Notification.status == "pending").scalar()

    return NotificationStatsResponse(
        total=total,
        sent=sent,
        failed=failed,
        pending=pending,
    )
