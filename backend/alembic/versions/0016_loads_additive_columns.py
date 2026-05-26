"""loads: additive columns (addresses fks, pricing, requirements, etc.)

Revision ID: 0016_loads_add
Revises: 0015_load_enum
Create Date: 2026-05-26 00:00:07.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0016_loads_add"
down_revision: Union[str, Sequence[str], None] = "0015_load_enum"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    dropoff_kind = sa.Enum(
        "delivery", "disposal", "donation", "recycling", "storage", "other",
        name="dropoffkind",
    )
    dropoff_kind.create(bind, checkfirst=True)

    pricing_mode = sa.Enum(
        "platform_quote", "customer_offer", "open_bidding", name="pricingmode"
    )
    pricing_mode.create(bind, checkfirst=True)

    visibility = sa.Enum("public", "invite_only", name="loadvisibility")
    visibility.create(bind, checkfirst=True)

    op.add_column("loads", sa.Column("reference_code", sa.String(length=12), nullable=True))
    op.create_unique_constraint("uq_loads_reference_code", "loads", ["reference_code"])

    op.add_column("loads", sa.Column("vehicle_id", sa.String(length=36), nullable=True))
    op.create_foreign_key(
        "fk_loads_vehicle_id", "loads", "vehicles", ["vehicle_id"], ["id"], ondelete="SET NULL"
    )

    op.add_column("loads", sa.Column("pickup_address_id", sa.String(length=36), nullable=True))
    op.create_foreign_key(
        "fk_loads_pickup_address_id",
        "loads",
        "addresses",
        ["pickup_address_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    op.add_column("loads", sa.Column("dropoff_address_id", sa.String(length=36), nullable=True))
    op.create_foreign_key(
        "fk_loads_dropoff_address_id",
        "loads",
        "addresses",
        ["dropoff_address_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    op.add_column(
        "loads",
        sa.Column(
            "dropoff_kind",
            sa.Enum(name="dropoffkind", create_type=False),
            server_default="delivery",
            nullable=False,
        ),
    )

    op.add_column("loads", sa.Column("volume_cuft", sa.Integer(), nullable=True))
    op.add_column("loads", sa.Column("item_count", sa.Integer(), nullable=True))

    op.add_column(
        "loads",
        sa.Column("requires_lift_gate", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column(
        "loads",
        sa.Column("requires_two_movers", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column(
        "loads",
        sa.Column("contains_hazardous", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column("loads", sa.Column("disposal_fee_estimate_cents", sa.BigInteger(), nullable=True))

    op.add_column(
        "loads",
        sa.Column(
            "pricing_mode",
            sa.Enum(name="pricingmode", create_type=False),
            server_default="platform_quote",
            nullable=False,
        ),
    )
    op.add_column("loads", sa.Column("accepted_price_cents", sa.BigInteger(), nullable=True))
    op.add_column(
        "loads",
        sa.Column("currency", sa.CHAR(length=3), server_default="USD", nullable=False),
    )

    op.add_column("loads", sa.Column("cancellation_reason", sa.String(length=2048), nullable=True))
    op.add_column("loads", sa.Column("cancelled_by_user_id", sa.String(length=36), nullable=True))
    op.create_foreign_key(
        "fk_loads_cancelled_by_user_id",
        "loads",
        "users",
        ["cancelled_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column("loads", sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))

    op.add_column(
        "loads",
        sa.Column(
            "visibility",
            sa.Enum(name="loadvisibility", create_type=False),
            server_default="public",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("loads", "visibility")
    op.drop_column("loads", "expires_at")
    op.drop_constraint("fk_loads_cancelled_by_user_id", "loads", type_="foreignkey")
    op.drop_column("loads", "cancelled_by_user_id")
    op.drop_column("loads", "cancellation_reason")
    op.drop_column("loads", "currency")
    op.drop_column("loads", "accepted_price_cents")
    op.drop_column("loads", "pricing_mode")
    op.drop_column("loads", "disposal_fee_estimate_cents")
    op.drop_column("loads", "contains_hazardous")
    op.drop_column("loads", "requires_two_movers")
    op.drop_column("loads", "requires_lift_gate")
    op.drop_column("loads", "item_count")
    op.drop_column("loads", "volume_cuft")
    op.drop_column("loads", "dropoff_kind")
    op.drop_constraint("fk_loads_dropoff_address_id", "loads", type_="foreignkey")
    op.drop_column("loads", "dropoff_address_id")
    op.drop_constraint("fk_loads_pickup_address_id", "loads", type_="foreignkey")
    op.drop_column("loads", "pickup_address_id")
    op.drop_constraint("fk_loads_vehicle_id", "loads", type_="foreignkey")
    op.drop_column("loads", "vehicle_id")
    op.drop_constraint("uq_loads_reference_code", "loads", type_="unique")
    op.drop_column("loads", "reference_code")

    sa.Enum(name="loadvisibility").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="pricingmode").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="dropoffkind").drop(op.get_bind(), checkfirst=True)
