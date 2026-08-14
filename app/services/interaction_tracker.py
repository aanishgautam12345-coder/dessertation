"""User interaction tracking service.

Tracks and manages user interactions with job recommendations:
- Views, saves, dismisses, applies
- Relevance judgments (mark relevant/irrelevant)
- Click-through tracking

This data feeds into the feedback loop to personalize future recommendations.

Usage:
    from app.services.interaction_tracker import InteractionTracker
    tracker = InteractionTracker(db)
    tracker.track_view(user_id, job_id)
    tracker.track_save(user_id, job_id)
    tracker.mark_relevant(user_id, job_id, relevance_score=3)
"""

import json
import logging
from datetime import datetime, timedelta
from collections import Counter
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.user_interaction import UserInteraction

logger = logging.getLogger(__name__)


class InteractionTracker:
    """Tracks and analyzes user interactions with job recommendations."""
    
    # Interaction types
    TYPE_IMPRESSION = "impression"
    TYPE_VIEW = "view"
    TYPE_SAVE = "save"
    TYPE_UNSAVE = "unsave"
    TYPE_DISMISS = "dismiss"
    TYPE_APPLY_CLICKED = "apply_clicked"
    TYPE_MARK_RELEVANT = "mark_relevant"
    TYPE_MARK_IRRELEVANT = "mark_irrelevant"
    
    def __init__(self, db: Session):
        self.db = db
    
    def track_interaction(
        self,
        user_id: int,
        job_id: int,
        interaction_type: str,
        metadata: dict | None = None,
    ) -> bool:
        """Track a user interaction."""
        try:
            interaction = UserInteraction(
                user_id=user_id,
                job_id=job_id,
                interaction_type=interaction_type,
                metadata=json.dumps(metadata) if metadata else None,
            )
            self.db.add(interaction)
            self.db.commit()
            
            logger.debug(f"Tracked interaction: user={user_id}, job={job_id}, type={interaction_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to track interaction: {e}")
            self.db.rollback()
            return False
    
    def track_impression(self, user_id: int, job_id: int) -> bool:
        """Track when a job is shown to a user."""
        return self.track_interaction(user_id, job_id, self.TYPE_IMPRESSION)
    
    def track_view(self, user_id: int, job_id: int) -> bool:
        """Track when a user views a job detail."""
        return self.track_interaction(user_id, job_id, self.TYPE_VIEW)
    
    def track_save(self, user_id: int, job_id: int) -> bool:
        """Track when a user saves a job."""
        return self.track_interaction(user_id, job_id, self.TYPE_SAVE)
    
    def track_unsave(self, user_id: int, job_id: int) -> bool:
        """Track when a user unsaves a job."""
        return self.track_interaction(user_id, job_id, self.TYPE_UNSAVE)
    
    def track_dismiss(self, user_id: int, job_id: int) -> bool:
        """Track when a user dismisses a recommendation."""
        return self.track_interaction(user_id, job_id, self.TYPE_DISMISS)
    
    def track_apply_clicked(self, user_id: int, job_id: int) -> bool:
        """Track when a user clicks to apply."""
        return self.track_interaction(user_id, job_id, self.TYPE_APPLY_CLICKED)
    
    def mark_relevant(self, user_id: int, job_id: int, score: int = 2) -> bool:
        """Mark a job as relevant (user provides explicit feedback)."""
        return self.track_interaction(
            user_id, job_id, self.TYPE_MARK_RELEVANT,
            metadata={"relevance_score": score}
        )
    
    def mark_irrelevant(self, user_id: int, job_id: int) -> bool:
        """Mark a job as irrelevant."""
        return self.track_interaction(user_id, job_id, self.TYPE_MARK_IRRELEVANT)
    
    def get_user_stats(self, user_id: int, days: int = 30) -> dict:
        """Get interaction statistics for a user."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        interactions = self.db.query(UserInteraction).filter(
            UserInteraction.user_id == user_id,
            UserInteraction.created_at >= cutoff,
        ).all()
        
        type_counts = Counter(i.interaction_type for i in interactions)
        
        # Compute engagement metrics
        total_impressions = type_counts.get(self.TYPE_IMPRESSION, 0)
        total_views = type_counts.get(self.TYPE_VIEW, 0)
        total_saves = type_counts.get(self.TYPE_SAVE, 0)
        total_dismisses = type_counts.get(self.TYPE_DISMISS, 0)
        total_applies = type_counts.get(self.TYPE_APPLY_CLICKED, 0)
        
        ctr = total_views / total_impressions if total_impressions > 0 else 0
        save_rate = total_saves / total_impressions if total_impressions > 0 else 0
        dismiss_rate = total_dismisses / total_impressions if total_impressions > 0 else 0
        apply_rate = total_applies / total_impressions if total_impressions > 0 else 0
        
        return {
            "user_id": user_id,
            "period_days": days,
            "total_interactions": len(interactions),
            "by_type": dict(type_counts),
            "impressions": total_impressions,
            "views": total_views,
            "saves": total_saves,
            "dismisses": total_dismisses,
            "applies": total_applies,
            "ctr": round(ctr, 3),
            "save_rate": round(save_rate, 3),
            "dismiss_rate": round(dismiss_rate, 3),
            "apply_rate": round(apply_rate, 3),
        }
    
    def get_job_stats(self, job_id: int) -> dict:
        """Get interaction statistics for a job across all users."""
        interactions = self.db.query(UserInteraction).filter(
            UserInteraction.job_id == job_id,
        ).all()
        
        type_counts = Counter(i.interaction_type for i in interactions)
        unique_users = len(set(i.user_id for i in interactions))
        
        return {
            "job_id": job_id,
            "total_interactions": len(interactions),
            "unique_users": unique_users,
            "by_type": dict(type_counts),
        }
    
    def get_recent_interactions(self, user_id: int, limit: int = 20) -> list[dict]:
        """Get recent interactions for a user."""
        interactions = self.db.query(UserInteraction).filter(
            UserInteraction.user_id == user_id,
        ).order_by(UserInteraction.created_at.desc()).limit(limit).all()
        
        return [
            {
                "id": str(i.id),
                "job_id": str(i.job_id),
                "type": i.interaction_type,
                "created_at": i.created_at.isoformat() if i.created_at else None,
                "metadata": json.loads(i.metadata) if i.metadata else None,
            }
            for i in interactions
        ]
