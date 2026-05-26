"""enable postgis extension

Revision ID: 0005_postgis
Revises: 24baab9295c0
Create Date: 2026-05-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "0005_postgis"
down_revision: Union[str, Sequence[str], None] = "24baab9295c0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS postgis")


def downgrade() -> None:
    # Leave the extension in place on downgrade — other objects may depend on it
    # and a fresh app DB shouldn't pay the cost of re-creating it.
    pass
