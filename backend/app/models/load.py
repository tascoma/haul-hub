import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, CHAR, DateTime, Enum, ForeignKey, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.databases import Base
from app.models.address import Address
from app.models.user import User
from app.models.vehicle import Vehicle


def _uuid() -> str:
    return str(uuid.uuid4())


class Urgency(str, enum.Enum):
    standard = "standard"
    express = "express"
    scheduled = "scheduled"


class LoadStatus(str, enum.Enum):
    draft = "draft"
    posted = "posted"
    bidding = "bidding"
    accepted = "accepted"
    en_route_to_pickup = "en_route_to_pickup"
    arrived_at_pickup = "arrived_at_pickup"
    picked_up = "picked_up"
    in_transit = "in_transit"
    arrived_at_dropoff = "arrived_at_dropoff"
    delivered = "delivered"
    cancelled = "cancelled"
    disputed = "disputed"


class DropoffKind(str, enum.Enum):
    delivery = "delivery"
    disposal = "disposal"
    donation = "donation"
    recycling = "recycling"
    storage = "storage"
    other = "other"


class PricingMode(str, enum.Enum):
    platform_quote = "platform_quote"
    customer_offer = "customer_offer"
    open_bidding = "open_bidding"


class LoadVisibility(str, enum.Enum):
    public = "public"
    invite_only = "invite_only"


class Load(Base):
    __tablename__ = "loads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)

    reference_code: Mapped[str | None] = mapped_column(String(12), unique=True)

    shipper_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    hauler_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    vehicle_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("vehicles.id", ondelete="SET NULL")
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(4096))
    photo_urls: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    # Item details
    weight_lbs: Mapped[int] = mapped_column(nullable=False)
    volume_cuft: Mapped[int | None]
    length_ft: Mapped[float | None]
    width_ft: Mapped[float | None]
    height_ft: Mapped[float | None]
    item_count: Mapped[int | None]

    # Requirements
    requires_lift_gate: Mapped[bool] = mapped_column(default=False, server_default=text("false"))
    requires_two_movers: Mapped[bool] = mapped_column(default=False, server_default=text("false"))
    contains_hazardous: Mapped[bool] = mapped_column(default=False, server_default=text("false"))
    disposal_fee_estimate_cents: Mapped[int | None]

    # Pickup (flat columns kept for frontend compatibility; FK is the source of truth going forward)
    pickup_address: Mapped[str] = mapped_column(String(255), nullable=False)
    pickup_city: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    pickup_state: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    pickup_zip: Mapped[str] = mapped_column(String(16), nullable=False)
    pickup_address_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("addresses.id", ondelete="RESTRICT"), nullable=False
    )
    pickup_window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    pickup_window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Dropoff (flat columns kept for frontend compatibility)
    dropoff_address: Mapped[str] = mapped_column(String(255), nullable=False)
    dropoff_city: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    dropoff_state: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    dropoff_zip: Mapped[str] = mapped_column(String(16), nullable=False)
    dropoff_address_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("addresses.id", ondelete="RESTRICT"), nullable=False
    )
    dropoff_by: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    dropoff_kind: Mapped[DropoffKind] = mapped_column(
        Enum(DropoffKind, name="dropoffkind"),
        default=DropoffKind.delivery,
        server_default=DropoffKind.delivery.value,
        nullable=False,
    )

    estimated_distance_miles: Mapped[float] = mapped_column(nullable=False)
    urgency: Mapped[Urgency] = mapped_column(Enum(Urgency, name="urgency"), nullable=False)

    pricing_mode: Mapped[PricingMode] = mapped_column(
        Enum(PricingMode, name="pricingmode"),
        default=PricingMode.platform_quote,
        server_default=PricingMode.platform_quote.value,
        nullable=False,
    )
    calculated_price_cents: Mapped[int] = mapped_column(nullable=False)
    accepted_price_cents: Mapped[int | None]
    currency: Mapped[str] = mapped_column(CHAR(3), default="USD", server_default="USD", nullable=False)

    status: Mapped[LoadStatus] = mapped_column(
        Enum(LoadStatus, name="loadstatus"),
        default=LoadStatus.posted,
        server_default=LoadStatus.posted.value,
        index=True,
        nullable=False,
    )

    visibility: Mapped[LoadVisibility] = mapped_column(
        Enum(LoadVisibility, name="loadvisibility"),
        default=LoadVisibility.public,
        server_default=LoadVisibility.public.value,
        nullable=False,
    )

    cancellation_reason: Mapped[str | None] = mapped_column(String(2048))
    cancelled_by_user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL")
    )

    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    picked_up_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    shipper: Mapped[User] = relationship(foreign_keys=[shipper_id], lazy="selectin")
    hauler: Mapped[User | None] = relationship(foreign_keys=[hauler_id], lazy="selectin")
    vehicle: Mapped[Vehicle | None] = relationship(foreign_keys=[vehicle_id], lazy="selectin")
    pickup_address_ref: Mapped[Address] = relationship(
        foreign_keys=[pickup_address_id], lazy="selectin"
    )
    dropoff_address_ref: Mapped[Address] = relationship(
        foreign_keys=[dropoff_address_id], lazy="selectin"
    )
