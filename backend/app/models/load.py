import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.databases import Base
from app.models.user import User


def _uuid() -> str:
    return str(uuid.uuid4())


class Urgency(str, enum.Enum):
    standard = "standard"
    express = "express"


class LoadStatus(str, enum.Enum):
    draft = "draft"
    posted = "posted"
    accepted = "accepted"
    picked_up = "picked_up"
    in_transit = "in_transit"
    delivered = "delivered"
    cancelled = "cancelled"


class Load(Base):
    __tablename__ = "loads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)

    shipper_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    hauler_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(4096))
    photo_urls: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    weight_lbs: Mapped[int] = mapped_column(nullable=False)
    length_ft: Mapped[float | None]
    width_ft: Mapped[float | None]
    height_ft: Mapped[float | None]

    pickup_address: Mapped[str] = mapped_column(String(255), nullable=False)
    pickup_city: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    pickup_state: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    pickup_zip: Mapped[str] = mapped_column(String(16), nullable=False)
    pickup_window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    pickup_window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    dropoff_address: Mapped[str] = mapped_column(String(255), nullable=False)
    dropoff_city: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    dropoff_state: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    dropoff_zip: Mapped[str] = mapped_column(String(16), nullable=False)
    dropoff_by: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    estimated_distance_miles: Mapped[float] = mapped_column(nullable=False)
    urgency: Mapped[Urgency] = mapped_column(Enum(Urgency), nullable=False)
    calculated_price_cents: Mapped[int] = mapped_column(nullable=False)

    status: Mapped[LoadStatus] = mapped_column(
        Enum(LoadStatus), default=LoadStatus.posted, server_default=LoadStatus.posted.value,
        index=True, nullable=False,
    )

    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    picked_up_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    shipper: Mapped[User] = relationship(foreign_keys=[shipper_id], lazy="selectin")
    hauler: Mapped[User | None] = relationship(foreign_keys=[hauler_id], lazy="selectin")
