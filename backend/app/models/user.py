import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
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
    other = "other"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
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
    phone: Mapped[str | None] = mapped_column(String(32))
    avatar_url: Mapped[str | None] = mapped_column(String(1024))
    shipper_enabled: Mapped[bool] = mapped_column(default=False, server_default="0")
    hauler_enabled: Mapped[bool] = mapped_column(default=False, server_default="0")
    stripe_account_id: Mapped[str | None] = mapped_column(String(64))
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
    vehicle_type: Mapped[VehicleType] = mapped_column(Enum(VehicleType), nullable=False)
    vehicle_make: Mapped[str | None] = mapped_column(String(64))
    vehicle_model: Mapped[str | None] = mapped_column(String(64))
    vehicle_year: Mapped[int | None]
    max_weight_lbs: Mapped[int | None]
    max_length_ft: Mapped[float | None]
    max_width_ft: Mapped[float | None]
    max_height_ft: Mapped[float | None]
    license_number: Mapped[str | None] = mapped_column(String(64))
    insurance_doc_url: Mapped[str | None] = mapped_column(String(1024))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="hauler_profile")
