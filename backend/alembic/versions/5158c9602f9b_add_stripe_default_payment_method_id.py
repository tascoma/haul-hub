"""add stripe_default_payment_method_id

Revision ID: 5158c9602f9b
Revises: 0018_loads_nn
Create Date: 2026-06-06 13:12:30.176086

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5158c9602f9b'
down_revision: Union[str, Sequence[str], None] = '0018_loads_nn'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('user_profiles', sa.Column('stripe_default_payment_method_id', sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column('user_profiles', 'stripe_default_payment_method_id')
