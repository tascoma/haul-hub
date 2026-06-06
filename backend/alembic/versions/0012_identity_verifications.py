"""identity_verifications

Revision ID: 0012_idv
Revises: 0011_docs
Create Date: 2026-05-26 00:00:03.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0012_idv"
down_revision: Union[str, Sequence[str], None] = "0011_docs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    kind = sa.Enum(
        "drivers_license",
        "passport",
        "business_doc",
        "stripe_identity",
        "insurance",
        "vehicle_registration",
        name="identityverificationkind",
    )
    kind.create(bind, checkfirst=True)

    status = sa.Enum(
        "pending", "approved", "rejected", "expired", name="identityverificationstatus"
    )
    status.create(bind, checkfirst=True)

    op.create_table(
        "identity_verifications",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column(
            "kind",
            sa.Enum(name="identityverificationkind", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(name="identityverificationstatus", create_type=False),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("provider", sa.String(length=64), nullable=True),
        sa.Column("provider_reference", sa.String(length=128), nullable=True),
        sa.Column("document_url", sa.String(length=1024), nullable=True),
        sa.Column("issuing_country", sa.CHAR(length=2), nullable=True),
        sa.Column("issuing_state", sa.String(length=32), nullable=True),
        sa.Column("expires_on", sa.Date(), nullable=True),
        sa.Column("reviewer_user_id", sa.String(length=36), nullable=True),
        sa.Column("review_notes", sa.String(length=2048), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewer_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_identity_verifications_user_id", "identity_verifications", ["user_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_identity_verifications_user_id", table_name="identity_verifications")
    op.drop_table("identity_verifications")
    sa.Enum(name="identityverificationstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="identityverificationkind").drop(op.get_bind(), checkfirst=True)
