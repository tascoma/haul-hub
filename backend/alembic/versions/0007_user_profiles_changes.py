"""user_profiles additions and stripe_account_id rename

Revision ID: 0007_profiles
Revises: 0006_users_id
Create Date: 2026-05-25 00:00:02.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0007_profiles"
down_revision: Union[str, Sequence[str], None] = "0006_users_id"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user_profiles", sa.Column("display_name", sa.String(length=64), nullable=True))
    op.add_column("user_profiles", sa.Column("bio", sa.String(length=2048), nullable=True))
    op.add_column(
        "user_profiles",
        sa.Column(
            "preferred_language",
            sa.String(length=8),
            server_default="en",
            nullable=False,
        ),
    )
    op.add_column(
        "user_profiles",
        sa.Column(
            "timezone",
            sa.String(length=64),
            server_default="America/Los_Angeles",
            nullable=False,
        ),
    )
    op.add_column(
        "user_profiles",
        sa.Column(
            "marketing_opt_in",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )
    op.add_column("user_profiles", sa.Column("stripe_customer_id", sa.String(length=64), nullable=True))
    op.alter_column("user_profiles", "stripe_account_id", new_column_name="stripe_connect_account_id")


def downgrade() -> None:
    op.alter_column("user_profiles", "stripe_connect_account_id", new_column_name="stripe_account_id")
    op.drop_column("user_profiles", "stripe_customer_id")
    op.drop_column("user_profiles", "marketing_opt_in")
    op.drop_column("user_profiles", "timezone")
    op.drop_column("user_profiles", "preferred_language")
    op.drop_column("user_profiles", "bio")
    op.drop_column("user_profiles", "display_name")
