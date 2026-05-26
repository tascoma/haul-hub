"""addresses and saved_addresses with PostGIS geom

Revision ID: 0008_addresses
Revises: 0007_profiles
Create Date: 2026-05-25 00:00:03.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0008_addresses"
down_revision: Union[str, Sequence[str], None] = "0007_profiles"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_GEOM_TRIGGER_UP = """
CREATE OR REPLACE FUNCTION addresses_set_geom() RETURNS trigger AS $$
BEGIN
    IF NEW.lat IS NOT NULL AND NEW.lng IS NOT NULL THEN
        NEW.geom := ST_SetSRID(ST_MakePoint(NEW.lng, NEW.lat), 4326)::geography;
    ELSE
        NEW.geom := NULL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS addresses_geom_trigger ON addresses;
CREATE TRIGGER addresses_geom_trigger
    BEFORE INSERT OR UPDATE OF lat, lng ON addresses
    FOR EACH ROW EXECUTE FUNCTION addresses_set_geom();
"""

_GEOM_TRIGGER_DOWN = """
DROP TRIGGER IF EXISTS addresses_geom_trigger ON addresses;
DROP FUNCTION IF EXISTS addresses_set_geom();
"""


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    address_type_hint = sa.Enum(
        "residential",
        "commercial",
        "industrial",
        "dump",
        "donation_center",
        "transfer_station",
        "storage",
        "other",
        name="addresstypehint",
    )
    address_type_hint.create(bind, checkfirst=True)

    op.create_table(
        "addresses",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("line1", sa.String(length=255), nullable=False),
        sa.Column("line2", sa.String(length=255), nullable=True),
        sa.Column("city", sa.String(length=128), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("postal_code", sa.String(length=16), nullable=False),
        sa.Column("country", sa.CHAR(length=2), server_default="US", nullable=False),
        sa.Column("lat", sa.Numeric(9, 6), nullable=True),
        sa.Column("lng", sa.Numeric(9, 6), nullable=True),
        sa.Column("place_id", sa.String(length=128), nullable=True),
        sa.Column("address_type_hint", address_type_hint, nullable=True),
        sa.Column("gate_code", sa.String(length=32), nullable=True),
        sa.Column("access_notes", sa.String(length=2048), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_addresses_city", "addresses", ["city"])
    op.create_index("ix_addresses_state", "addresses", ["state"])

    if is_postgres:
        # Add the PostGIS column + trigger only where PostGIS exists. Keeps the
        # ORM model dialect-agnostic — the app reads lat/lng; radius queries
        # hit `geom` via raw SQL.
        op.execute("ALTER TABLE addresses ADD COLUMN geom geography(Point, 4326)")
        op.execute(
            "CREATE INDEX ix_addresses_geom ON addresses USING GIST (geom)"
        )
        op.execute(_GEOM_TRIGGER_UP)

    op.create_table(
        "saved_addresses",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("address_id", sa.String(length=36), nullable=False),
        sa.Column("label", sa.String(length=64), nullable=False),
        sa.Column(
            "is_default_pickup",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "is_default_dropoff",
            sa.Boolean(),
            server_default=sa.text("false"),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["address_id"], ["addresses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_saved_addresses_user_id", "saved_addresses", ["user_id"])
    op.create_index(
        "uq_saved_addresses_default_pickup",
        "saved_addresses",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("is_default_pickup = true"),
    )
    op.create_index(
        "uq_saved_addresses_default_dropoff",
        "saved_addresses",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("is_default_dropoff = true"),
    )


def downgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    op.drop_index("uq_saved_addresses_default_dropoff", table_name="saved_addresses")
    op.drop_index("uq_saved_addresses_default_pickup", table_name="saved_addresses")
    op.drop_index("ix_saved_addresses_user_id", table_name="saved_addresses")
    op.drop_table("saved_addresses")

    if is_postgres:
        op.execute(_GEOM_TRIGGER_DOWN)
        op.execute("DROP INDEX IF EXISTS ix_addresses_geom")
    op.drop_index("ix_addresses_state", table_name="addresses")
    op.drop_index("ix_addresses_city", table_name="addresses")
    op.drop_table("addresses")
    sa.Enum(name="addresstypehint").drop(bind, checkfirst=True)
