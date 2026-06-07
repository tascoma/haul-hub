"""stripe connect capability flags and webhook event dedup

Revision ID: b1f2c3d4e5a6
Revises: a30887d1ccd1
Create Date: 2026-06-06 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1f2c3d4e5a6'
down_revision: Union[str, Sequence[str], None] = 'a30887d1ccd1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_profiles",
        sa.Column("stripe_charges_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "user_profiles",
        sa.Column("stripe_payouts_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "user_profiles",
        sa.Column("stripe_details_submitted", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_table(
        "processed_webhook_events",
        sa.Column("event_id", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("event_id"),
    )


def downgrade() -> None:
    op.drop_table("processed_webhook_events")
    op.drop_column("user_profiles", "stripe_details_submitted")
    op.drop_column("user_profiles", "stripe_payouts_enabled")
    op.drop_column("user_profiles", "stripe_charges_enabled")
