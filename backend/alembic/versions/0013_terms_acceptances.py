"""terms_acceptances

Revision ID: 0013_terms
Revises: 0012_idv
Create Date: 2026-05-26 00:00:04.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0013_terms"
down_revision: Union[str, Sequence[str], None] = "0012_idv"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    kind = sa.Enum(
        "terms_of_service", "privacy_policy", "hauler_agreement", name="termsdocumentkind"
    )
    kind.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "terms_acceptances",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column(
            "document_kind",
            sa.Enum(name="termsdocumentkind", create_type=False),
            nullable=False,
        ),
        sa.Column("version", sa.String(length=32), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_terms_acceptances_user_id", "terms_acceptances", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_terms_acceptances_user_id", table_name="terms_acceptances")
    op.drop_table("terms_acceptances")
    sa.Enum(name="termsdocumentkind").drop(op.get_bind(), checkfirst=True)
