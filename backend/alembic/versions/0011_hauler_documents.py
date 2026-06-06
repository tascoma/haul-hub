"""hauler_documents

Revision ID: 0011_docs
Revises: 0010_hauler_pr
Create Date: 2026-05-26 00:00:02.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0011_docs"
down_revision: Union[str, Sequence[str], None] = "0010_hauler_pr"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    kind = sa.Enum(
        "insurance_certificate",
        "vehicle_registration",
        "business_license",
        "dot_authority",
        "workers_comp",
        "other",
        name="haulerdocumentkind",
    )
    kind.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "hauler_documents",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("hauler_user_id", sa.String(length=36), nullable=False),
        sa.Column("vehicle_id", sa.String(length=36), nullable=True),
        sa.Column("kind", sa.Enum(name="haulerdocumentkind", create_type=False), nullable=False),
        sa.Column("document_url", sa.String(length=1024), nullable=False),
        sa.Column("policy_number", sa.String(length=64), nullable=True),
        sa.Column("carrier_name", sa.String(length=128), nullable=True),
        sa.Column("coverage_amount_cents", sa.BigInteger(), nullable=True),
        sa.Column("effective_on", sa.Date(), nullable=True),
        sa.Column("expires_on", sa.Date(), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["hauler_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_hauler_documents_user_kind_expiry",
        "hauler_documents",
        ["hauler_user_id", "kind", "expires_on"],
    )


def downgrade() -> None:
    op.drop_index("ix_hauler_documents_user_kind_expiry", table_name="hauler_documents")
    op.drop_table("hauler_documents")
    sa.Enum(name="haulerdocumentkind").drop(op.get_bind(), checkfirst=True)
