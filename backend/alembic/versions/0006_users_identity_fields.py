"""users identity fields

Revision ID: 0006_users_id
Revises: 0005_postgis
Create Date: 2026-05-25 00:00:01.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0006_users_id"
down_revision: Union[str, Sequence[str], None] = "0005_postgis"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("phone", sa.String(length=32), nullable=True))
    op.add_column("users", sa.Column("phone_verified_at", sa.DateTime(timezone=True), nullable=True))

    user_status = sa.Enum(
        "active", "suspended", "deleted", name="userstatus"
    )
    user_status.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "users",
        sa.Column(
            "status",
            user_status,
            server_default="active",
            nullable=False,
        ),
    )

    op.add_column("users", sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))

    op.create_index(
        "ix_users_phone_unique",
        "users",
        ["phone"],
        unique=True,
        postgresql_where=sa.text("phone IS NOT NULL"),
    )
    op.create_index("ix_users_status_created_at", "users", ["status", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_users_status_created_at", table_name="users")
    op.drop_index("ix_users_phone_unique", table_name="users")
    op.drop_column("users", "deleted_at")
    op.drop_column("users", "last_login_at")
    op.drop_column("users", "status")
    sa.Enum(name="userstatus").drop(op.get_bind(), checkfirst=True)
    op.drop_column("users", "phone_verified_at")
    op.drop_column("users", "phone")
    op.drop_column("users", "email_verified_at")
