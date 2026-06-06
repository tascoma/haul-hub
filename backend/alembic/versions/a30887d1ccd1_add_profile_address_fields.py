"""add_profile_address_fields

Revision ID: a30887d1ccd1
Revises: 5158c9602f9b
Create Date: 2026-06-06 14:54:00.391109

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a30887d1ccd1'
down_revision: Union[str, Sequence[str], None] = '5158c9602f9b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user_profiles", sa.Column("address_line1", sa.String(255), nullable=True))
    op.add_column("user_profiles", sa.Column("address_city", sa.String(100), nullable=True))
    op.add_column("user_profiles", sa.Column("address_state", sa.String(2), nullable=True))
    op.add_column("user_profiles", sa.Column("address_zip", sa.String(10), nullable=True))
    op.add_column(
        "user_profiles",
        sa.Column("billing_same_as_home", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column("user_profiles", sa.Column("billing_address_line1", sa.String(255), nullable=True))
    op.add_column("user_profiles", sa.Column("billing_address_city", sa.String(100), nullable=True))
    op.add_column("user_profiles", sa.Column("billing_address_state", sa.String(2), nullable=True))
    op.add_column("user_profiles", sa.Column("billing_address_zip", sa.String(10), nullable=True))


def downgrade() -> None:
    op.drop_column("user_profiles", "billing_address_zip")
    op.drop_column("user_profiles", "billing_address_state")
    op.drop_column("user_profiles", "billing_address_city")
    op.drop_column("user_profiles", "billing_address_line1")
    op.drop_column("user_profiles", "billing_same_as_home")
    op.drop_column("user_profiles", "address_zip")
    op.drop_column("user_profiles", "address_state")
    op.drop_column("user_profiles", "address_city")
    op.drop_column("user_profiles", "address_line1")
