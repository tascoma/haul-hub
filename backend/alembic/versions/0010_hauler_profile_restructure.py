"""restructure hauler_profiles: drop vehicle cols, add ops fields

Revision ID: 0010_hauler_pr
Revises: 0009_vehicles
Create Date: 2026-05-26 00:00:01.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0010_hauler_pr"
down_revision: Union[str, Sequence[str], None] = "0009_vehicles"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    business_type = sa.Enum(
        "individual", "llc", "corporation", "partnership", name="businesstype"
    )
    business_type.create(bind, checkfirst=True)

    # Add new operational fields.
    op.add_column("hauler_profiles", sa.Column("company_name", sa.String(length=255), nullable=True))
    op.add_column(
        "hauler_profiles",
        sa.Column("business_type", sa.Enum(name="businesstype", create_type=False), nullable=True),
    )
    op.add_column("hauler_profiles", sa.Column("tax_id_last4", sa.String(length=4), nullable=True))
    op.add_column("hauler_profiles", sa.Column("years_experience", sa.Integer(), nullable=True))
    op.add_column("hauler_profiles", sa.Column("bio", sa.String(length=2048), nullable=True))
    op.add_column(
        "hauler_profiles",
        sa.Column("home_base_address_id", sa.String(length=36), nullable=True),
    )
    op.create_foreign_key(
        "fk_hauler_profiles_home_base_address",
        "hauler_profiles",
        "addresses",
        ["home_base_address_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column(
        "hauler_profiles",
        sa.Column("service_radius_miles", sa.Integer(), server_default="25", nullable=False),
    )
    op.add_column(
        "hauler_profiles",
        sa.Column(
            "accepts_disposal_jobs",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
    )
    op.add_column(
        "hauler_profiles",
        sa.Column(
            "accepts_donation_runs",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
    )
    op.add_column(
        "hauler_profiles",
        sa.Column(
            "accepts_hazardous",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )
    op.add_column(
        "hauler_profiles",
        sa.Column(
            "currently_available",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )
    op.add_column(
        "hauler_profiles",
        sa.Column("auto_accept_under_cents", sa.BigInteger(), nullable=True),
    )
    op.add_column("hauler_profiles", sa.Column("rating_avg", sa.Float(), nullable=True))
    op.add_column(
        "hauler_profiles",
        sa.Column("rating_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "hauler_profiles",
        sa.Column("jobs_completed", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column("hauler_profiles", sa.Column("suspended_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("hauler_profiles", sa.Column("suspension_reason", sa.String(length=1024), nullable=True))

    # Drop the old vehicle columns — data already migrated to `vehicles`.
    op.drop_column("hauler_profiles", "insurance_doc_url")
    op.drop_column("hauler_profiles", "license_number")
    op.drop_column("hauler_profiles", "max_height_ft")
    op.drop_column("hauler_profiles", "max_width_ft")
    op.drop_column("hauler_profiles", "max_length_ft")
    op.drop_column("hauler_profiles", "max_weight_lbs")
    op.drop_column("hauler_profiles", "vehicle_year")
    op.drop_column("hauler_profiles", "vehicle_model")
    op.drop_column("hauler_profiles", "vehicle_make")
    op.drop_column("hauler_profiles", "vehicle_type")


def downgrade() -> None:
    # Re-add old vehicle columns (nullable since we cannot reliably recover values).
    op.add_column(
        "hauler_profiles",
        sa.Column(
            "vehicle_type",
            sa.Enum(name="vehicletype", create_type=False),
            nullable=True,
        ),
    )
    op.add_column("hauler_profiles", sa.Column("vehicle_make", sa.String(length=64), nullable=True))
    op.add_column("hauler_profiles", sa.Column("vehicle_model", sa.String(length=64), nullable=True))
    op.add_column("hauler_profiles", sa.Column("vehicle_year", sa.Integer(), nullable=True))
    op.add_column("hauler_profiles", sa.Column("max_weight_lbs", sa.Integer(), nullable=True))
    op.add_column("hauler_profiles", sa.Column("max_length_ft", sa.Float(), nullable=True))
    op.add_column("hauler_profiles", sa.Column("max_width_ft", sa.Float(), nullable=True))
    op.add_column("hauler_profiles", sa.Column("max_height_ft", sa.Float(), nullable=True))
    op.add_column("hauler_profiles", sa.Column("license_number", sa.String(length=64), nullable=True))
    op.add_column("hauler_profiles", sa.Column("insurance_doc_url", sa.String(length=1024), nullable=True))

    op.drop_column("hauler_profiles", "suspension_reason")
    op.drop_column("hauler_profiles", "suspended_at")
    op.drop_column("hauler_profiles", "jobs_completed")
    op.drop_column("hauler_profiles", "rating_count")
    op.drop_column("hauler_profiles", "rating_avg")
    op.drop_column("hauler_profiles", "auto_accept_under_cents")
    op.drop_column("hauler_profiles", "currently_available")
    op.drop_column("hauler_profiles", "accepts_hazardous")
    op.drop_column("hauler_profiles", "accepts_donation_runs")
    op.drop_column("hauler_profiles", "accepts_disposal_jobs")
    op.drop_column("hauler_profiles", "service_radius_miles")
    op.drop_constraint("fk_hauler_profiles_home_base_address", "hauler_profiles", type_="foreignkey")
    op.drop_column("hauler_profiles", "home_base_address_id")
    op.drop_column("hauler_profiles", "bio")
    op.drop_column("hauler_profiles", "years_experience")
    op.drop_column("hauler_profiles", "tax_id_last4")
    op.drop_column("hauler_profiles", "business_type")
    op.drop_column("hauler_profiles", "company_name")
    sa.Enum(name="businesstype").drop(op.get_bind(), checkfirst=True)
