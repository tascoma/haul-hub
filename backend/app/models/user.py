import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.databases import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class VehicleType(str, enum.Enum):
    pickup = "pickup"
    pickup_with_trailer = "pickup_with_trailer"
    flatbed = "flatbed"
    box_truck = "box_truck"
    cargo_van = "cargo_van"
    semi = "semi"
    dump_truck = "dump_truck"
    roll_off = "roll_off"
    other = "other"


class UserStatus(str, enum.Enum):
    active = "active"
    suspended = "suspended"
    deleted = "deleted"


class BusinessType(str, enum.Enum):
    individual = "individual"
    llc = "llc"
    corporation = "corporation"
    partnership = "partnership"


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index(
            "ix_users_phone_unique",
            "phone",
            unique=True,
            postgresql_where=text("phone IS NOT NULL"),
            sqlite_where=text("phone IS NOT NULL"),
        ),
        Index("ix_users_status_created_at", "status", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    phone: Mapped[str | None] = mapped_column(String(32))
    phone_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, name="userstatus"),
        default=UserStatus.active,
        server_default=UserStatus.active.value,
        nullable=False,
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    profile: Mapped["UserProfile"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan", lazy="selectin"
    )
    hauler_profile: Mapped["HaulerProfile | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan", lazy="selectin"
    )


class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    full_name: Mapped[str | None] = mapped_column(String(255))
    display_name: Mapped[str | None] = mapped_column(String(64))
    phone: Mapped[str | None] = mapped_column(String(32))
    avatar_url: Mapped[str | None] = mapped_column(String(1024))
    bio: Mapped[str | None] = mapped_column(String(2048))
    preferred_language: Mapped[str] = mapped_column(
        String(8), default="en", server_default="en", nullable=False
    )
    timezone: Mapped[str] = mapped_column(
        String(64), default="America/Los_Angeles", server_default="America/Los_Angeles", nullable=False
    )
    shipper_enabled: Mapped[bool] = mapped_column(default=False, server_default=text("false"))
    hauler_enabled: Mapped[bool] = mapped_column(default=False, server_default=text("false"))
    marketing_opt_in: Mapped[bool] = mapped_column(default=False, server_default=text("false"))
    stripe_customer_id: Mapped[str | None] = mapped_column(String(64))
    stripe_connect_account_id: Mapped[str | None] = mapped_column(String(64))
    stripe_default_payment_method_id: Mapped[str | None] = mapped_column(String(64))
    address_line1: Mapped[str | None] = mapped_column(String(255))
    address_city: Mapped[str | None] = mapped_column(String(100))
    address_state: Mapped[str | None] = mapped_column(String(2))
    address_zip: Mapped[str | None] = mapped_column(String(10))
    billing_same_as_home: Mapped[bool] = mapped_column(default=True, server_default=text("true"))
    billing_address_line1: Mapped[str | None] = mapped_column(String(255))
    billing_address_city: Mapped[str | None] = mapped_column(String(100))
    billing_address_state: Mapped[str | None] = mapped_column(String(2))
    billing_address_zip: Mapped[str | None] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="profile")


class HaulerProfile(Base):
    __tablename__ = "hauler_profiles"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    company_name: Mapped[str | None] = mapped_column(String(255))
    business_type: Mapped[BusinessType | None] = mapped_column(Enum(BusinessType, name="businesstype"))
    tax_id_last4: Mapped[str | None] = mapped_column(String(4))
    years_experience: Mapped[int | None]
    bio: Mapped[str | None] = mapped_column(String(2048))
    home_base_address_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("addresses.id", ondelete="SET NULL")
    )
    service_radius_miles: Mapped[int] = mapped_column(default=25, server_default="25", nullable=False)
    accepts_disposal_jobs: Mapped[bool] = mapped_column(default=True, server_default=text("true"))
    accepts_donation_runs: Mapped[bool] = mapped_column(default=True, server_default=text("true"))
    accepts_hazardous: Mapped[bool] = mapped_column(default=False, server_default=text("false"))
    currently_available: Mapped[bool] = mapped_column(default=False, server_default=text("false"))
    auto_accept_under_cents: Mapped[int | None]
    rating_avg: Mapped[float | None]
    rating_count: Mapped[int] = mapped_column(default=0, server_default="0", nullable=False)
    jobs_completed: Mapped[int] = mapped_column(default=0, server_default="0", nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    suspended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    suspension_reason: Mapped[str | None] = mapped_column(String(1024))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="hauler_profile")
