"""loads: backfill addresses table from flat pickup/dropoff fields,
generate reference_code for existing rows

Revision ID: 0017_loads_bf
Revises: 0016_loads_add
Create Date: 2026-05-26 00:00:08.000000

"""
from typing import Sequence, Union
import secrets
import string
import uuid

from alembic import op
import sqlalchemy as sa


revision: str = "0017_loads_bf"
down_revision: Union[str, Sequence[str], None] = "0016_loads_add"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Crockford-base32 minus the easily-confused characters (I, L, O, U).
_REF_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def _ref_code() -> str:
    suffix = "".join(secrets.choice(_REF_ALPHABET) for _ in range(8))
    return f"HH-{suffix[:5]}{suffix[5:]}"[:12]


def upgrade() -> None:
    bind = op.get_bind()

    loads = sa.table(
        "loads",
        sa.column("id", sa.String),
        sa.column("reference_code", sa.String),
        sa.column("pickup_address", sa.String),
        sa.column("pickup_city", sa.String),
        sa.column("pickup_state", sa.String),
        sa.column("pickup_zip", sa.String),
        sa.column("pickup_address_id", sa.String),
        sa.column("dropoff_address", sa.String),
        sa.column("dropoff_city", sa.String),
        sa.column("dropoff_state", sa.String),
        sa.column("dropoff_zip", sa.String),
        sa.column("dropoff_address_id", sa.String),
    )
    addresses = sa.table(
        "addresses",
        sa.column("id", sa.String),
        sa.column("line1", sa.String),
        sa.column("city", sa.String),
        sa.column("state", sa.String),
        sa.column("postal_code", sa.String),
    )

    existing = bind.execute(
        sa.select(
            loads.c.id,
            loads.c.reference_code,
            loads.c.pickup_address,
            loads.c.pickup_city,
            loads.c.pickup_state,
            loads.c.pickup_zip,
            loads.c.dropoff_address,
            loads.c.dropoff_city,
            loads.c.dropoff_state,
            loads.c.dropoff_zip,
        )
    ).all()

    # Cache reusable address rows so we don't double-insert identical addresses.
    address_cache: dict[tuple[str, str, str, str], str] = {}

    def _find_or_create(
        line1: str, city: str, state: str, postal_code: str
    ) -> str:
        key = (line1 or "", city or "", state or "", postal_code or "")
        if key in address_cache:
            return address_cache[key]

        match = bind.execute(
            sa.select(addresses.c.id).where(
                sa.and_(
                    addresses.c.line1 == line1,
                    addresses.c.city == city,
                    addresses.c.state == state,
                    addresses.c.postal_code == postal_code,
                )
            )
        ).first()
        if match:
            address_cache[key] = match.id
            return match.id

        new_id = str(uuid.uuid4())
        bind.execute(
            addresses.insert().values(
                id=new_id,
                line1=line1,
                city=city,
                state=state,
                postal_code=postal_code,
            )
        )
        address_cache[key] = new_id
        return new_id

    for load in existing:
        pickup_id = _find_or_create(
            load.pickup_address, load.pickup_city, load.pickup_state, load.pickup_zip
        )
        dropoff_id = _find_or_create(
            load.dropoff_address, load.dropoff_city, load.dropoff_state, load.dropoff_zip
        )
        ref = load.reference_code or _ref_code()
        bind.execute(
            loads.update()
            .where(loads.c.id == load.id)
            .values(
                pickup_address_id=pickup_id,
                dropoff_address_id=dropoff_id,
                reference_code=ref,
            )
        )


def downgrade() -> None:
    # Backfill is data only; the columns themselves are dropped by 0016 downgrade.
    pass
