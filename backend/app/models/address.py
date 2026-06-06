import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    CHAR,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.databases import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class AddressTypeHint(str, enum.Enum):
    residential = "residential"
    commercial = "commercial"
    industrial = "industrial"
    dump = "dump"
    donation_center = "donation_center"
    transfer_station = "transfer_station"
    storage = "storage"
    other = "other"


class Address(Base):
    """Normalized address row.

    The `geom geography(Point, 4326)` column lives in Postgres (added by migration
    0008 and kept in sync with `lat`/`lng` by a DB trigger). It's intentionally
    NOT mapped on the ORM model so SQLite can drop/recreate this table for tests
    without needing PostGIS. Radius queries hit `geom` via raw SQL.
    """

    __tablename__ = "addresses"
    __table_args__ = (
        Index("ix_addresses_city", "city"),
        Index("ix_addresses_state", "state"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    line1: Mapped[str] = mapped_column(String(255), nullable=False)
    line2: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str] = mapped_column(String(128), nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(16), nullable=False)
    country: Mapped[str] = mapped_column(CHAR(2), default="US", server_default="US", nullable=False)
    lat: Mapped[float | None] = mapped_column(Numeric(9, 6))
    lng: Mapped[float | None] = mapped_column(Numeric(9, 6))
    place_id: Mapped[str | None] = mapped_column(String(128))
    address_type_hint: Mapped[AddressTypeHint | None] = mapped_column(
        Enum(AddressTypeHint, name="addresstypehint")
    )
    gate_code: Mapped[str | None] = mapped_column(String(32))
    access_notes: Mapped[str | None] = mapped_column(String(2048))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SavedAddress(Base):
    __tablename__ = "saved_addresses"
    __table_args__ = (
        Index(
            "uq_saved_addresses_default_pickup",
            "user_id",
            unique=True,
            postgresql_where=text("is_default_pickup = true"),
            sqlite_where=text("is_default_pickup = 1"),
        ),
        Index(
            "uq_saved_addresses_default_dropoff",
            "user_id",
            unique=True,
            postgresql_where=text("is_default_dropoff = true"),
            sqlite_where=text("is_default_dropoff = 1"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    address_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("addresses.id", ondelete="CASCADE"), nullable=False
    )
    label: Mapped[str] = mapped_column(String(64), nullable=False)
    is_default_pickup: Mapped[bool] = mapped_column(default=False, server_default=text("false"))
    is_default_dropoff: Mapped[bool] = mapped_column(default=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    address: Mapped[Address] = relationship(lazy="selectin")
