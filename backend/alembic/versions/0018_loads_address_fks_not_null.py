"""loads: make address FKs NOT NULL after backfill

Revision ID: 0018_loads_nn
Revises: 0017_loads_bf
Create Date: 2026-05-26 00:00:09.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "0018_loads_nn"
down_revision: Union[str, Sequence[str], None] = "0017_loads_bf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("loads", "pickup_address_id", nullable=False)
    op.alter_column("loads", "dropoff_address_id", nullable=False)


def downgrade() -> None:
    op.alter_column("loads", "dropoff_address_id", nullable=True)
    op.alter_column("loads", "pickup_address_id", nullable=True)
