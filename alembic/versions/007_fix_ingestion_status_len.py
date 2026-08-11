"""Widen ingestion_runs.status to fit 'completed_with_errors'.

Revision ID: 007_fix_ingestion_status_len
Revises: 006_phase3_notifications
"""

from alembic import op
import sqlalchemy as sa

revision = "007_fix_ingestion_status_len"
down_revision = "006_phase3_notifications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "ingestion_runs", "status",
        existing_type=sa.String(20), type_=sa.String(30),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "ingestion_runs", "status",
        existing_type=sa.String(30), type_=sa.String(20),
        existing_nullable=True,
    )
