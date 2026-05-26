"""extend loadstatus enum and add urgency.scheduled

Revision ID: 0015_load_enum
Revises: 0014_areas
Create Date: 2026-05-26 00:00:06.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "0015_load_enum"
down_revision: Union[str, Sequence[str], None] = "0014_areas"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_NEW_LOAD_STATUSES = [
    "bidding",
    "en_route_to_pickup",
    "arrived_at_pickup",
    "arrived_at_dropoff",
    "disputed",
]


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    # ALTER TYPE ... ADD VALUE cannot run inside a transaction block. Alembic
    # wraps migrations in a transaction by default, so commit first.
    op.execute("COMMIT")
    for value in _NEW_LOAD_STATUSES:
        op.execute(f"ALTER TYPE loadstatus ADD VALUE IF NOT EXISTS '{value}'")
    op.execute("ALTER TYPE urgency ADD VALUE IF NOT EXISTS 'scheduled'")


def downgrade() -> None:
    # Postgres enums cannot drop values without recreating the type.
    # No-op: removing the new variants would require rewriting the table.
    pass
