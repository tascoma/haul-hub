"""create vehicles table and backfill from hauler_profiles

Revision ID: 0009_vehicles
Revises: 0008_addresses
Create Date: 2026-05-26 00:00:00.000000

"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa


revision: str = "0009_vehicles"
down_revision: Union[str, Sequence[str], None] = "0008_addresses"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    # Extend the existing vehicletype enum with the two new variants used by
    # the schema. Native PG enums require ADD VALUE in its own statement.
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE vehicletype ADD VALUE IF NOT EXISTS 'dump_truck'")
        op.execute("ALTER TYPE vehicletype ADD VALUE IF NOT EXISTS 'roll_off'")

    vehicle_status = sa.Enum("active", "inactive", "retired", name="vehiclestatus")
    vehicle_status.create(bind, checkfirst=True)

    op.create_table(
        "vehicles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("owner_user_id", sa.String(length=36), nullable=False),
        sa.Column("nickname", sa.String(length=64), nullable=True),
        sa.Column(
            "vehicle_type",
            sa.Enum(
                "pickup",
                "pickup_with_trailer",
                "flatbed",
                "box_truck",
                "cargo_van",
                "semi",
                "dump_truck",
                "roll_off",
                "other",
                name="vehicletype",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("make", sa.String(length=64), nullable=True),
        sa.Column("model", sa.String(length=64), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("color", sa.String(length=32), nullable=True),
        sa.Column("license_plate", sa.String(length=16), nullable=True),
        sa.Column("license_plate_state", sa.String(length=8), nullable=True),
        sa.Column("vin", sa.String(length=17), nullable=True),
        sa.Column("max_payload_lbs", sa.Integer(), nullable=True),
        sa.Column("max_volume_cuft", sa.Integer(), nullable=True),
        sa.Column("bed_length_ft", sa.Numeric(4, 1), nullable=True),
        sa.Column("bed_width_ft", sa.Numeric(4, 1), nullable=True),
        sa.Column("bed_height_ft", sa.Numeric(4, 1), nullable=True),
        sa.Column("has_lift_gate", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("has_dolly", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("has_straps", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("has_blankets", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_default", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "status",
            sa.Enum(name="vehiclestatus", create_type=False),
            server_default="active",
            nullable=False,
        ),
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
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_vehicles_owner", "vehicles", ["owner_user_id"])
    op.create_index(
        "uq_vehicles_default",
        "vehicles",
        ["owner_user_id"],
        unique=True,
        postgresql_where=sa.text("is_default = true"),
    )

    # Backfill: one row per existing hauler_profiles record, using whatever
    # vehicle data they had embedded.
    hp = sa.table(
        "hauler_profiles",
        sa.column("user_id", sa.String),
        sa.column("vehicle_type", sa.String),
        sa.column("vehicle_make", sa.String),
        sa.column("vehicle_model", sa.String),
        sa.column("vehicle_year", sa.Integer),
        sa.column("max_weight_lbs", sa.Integer),
    )
    existing = bind.execute(
        sa.select(
            hp.c.user_id,
            hp.c.vehicle_type,
            hp.c.vehicle_make,
            hp.c.vehicle_model,
            hp.c.vehicle_year,
            hp.c.max_weight_lbs,
        )
    ).all()

    if existing:
        v = sa.table(
            "vehicles",
            sa.column("id", sa.String),
            sa.column("owner_user_id", sa.String),
            sa.column("vehicle_type", sa.String),
            sa.column("make", sa.String),
            sa.column("model", sa.String),
            sa.column("year", sa.Integer),
            sa.column("max_payload_lbs", sa.Integer),
            sa.column("is_default", sa.Boolean),
            sa.column("status", sa.String),
        )
        rows = [
            {
                "id": str(uuid.uuid4()),
                "owner_user_id": row.user_id,
                "vehicle_type": row.vehicle_type or "other",
                "make": row.vehicle_make,
                "model": row.vehicle_model,
                "year": row.vehicle_year,
                "max_payload_lbs": row.max_weight_lbs,
                "is_default": True,
                "status": "active",
            }
            for row in existing
        ]
        op.bulk_insert(v, rows)


def downgrade() -> None:
    op.drop_index("uq_vehicles_default", table_name="vehicles")
    op.drop_index("ix_vehicles_owner", table_name="vehicles")
    op.drop_table("vehicles")
    sa.Enum(name="vehiclestatus").drop(op.get_bind(), checkfirst=True)
    # vehicletype enum is kept (it predates this migration); the new variants
    # cannot be removed in Postgres without recreating the type.
