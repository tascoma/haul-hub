"""service_areas

Revision ID: 0014_areas
Revises: 0013_terms
Create Date: 2026-05-26 00:00:05.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0014_areas"
down_revision: Union[str, Sequence[str], None] = "0013_terms"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    kind = sa.Enum("radius", "postal_code", "polygon", name="serviceareakind")
    kind.create(bind, checkfirst=True)

    op.create_table(
        "service_areas",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("hauler_user_id", sa.String(length=36), nullable=False),
        sa.Column(
            "kind",
            sa.Enum(name="serviceareakind", create_type=False),
            nullable=False,
        ),
        sa.Column("center_address_id", sa.String(length=36), nullable=True),
        sa.Column("radius_miles", sa.Integer(), nullable=True),
        sa.Column("postal_code", sa.String(length=16), nullable=True),
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
        sa.ForeignKeyConstraint(["center_address_id"], ["addresses.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_service_areas_hauler_user_id", "service_areas", ["hauler_user_id"])

    if is_postgres:
        op.execute(
            "ALTER TABLE service_areas ADD COLUMN polygon geography(Polygon, 4326)"
        )


def downgrade() -> None:
    op.drop_index("ix_service_areas_hauler_user_id", table_name="service_areas")
    op.drop_table("service_areas")
    sa.Enum(name="serviceareakind").drop(op.get_bind(), checkfirst=True)
