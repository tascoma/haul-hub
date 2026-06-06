import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.databases import Base
from app.models.user import VehicleType


def _uuid() -> str:
    return str(uuid.uuid4())


class VehicleStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    retired = "retired"


class Vehicle(Base):
    __tablename__ = "vehicles"
    __table_args__ = (
        Index(
            "uq_vehicles_default",
            "owner_user_id",
            unique=True,
            postgresql_where=text("is_default = true"),
            sqlite_where=text("is_default = 1"),
        ),
        Index("ix_vehicles_owner", "owner_user_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    owner_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    nickname: Mapped[str | None] = mapped_column(String(64))
    vehicle_type: Mapped[VehicleType] = mapped_column(Enum(VehicleType, name="vehicletype"), nullable=False)
    make: Mapped[str | None] = mapped_column(String(64))
    model: Mapped[str | None] = mapped_column(String(64))
    year: Mapped[int | None]
    color: Mapped[str | None] = mapped_column(String(32))
    license_plate: Mapped[str | None] = mapped_column(String(16))
    license_plate_state: Mapped[str | None] = mapped_column(String(8))
    vin: Mapped[str | None] = mapped_column(String(17))
    max_payload_lbs: Mapped[int | None]
    max_volume_cuft: Mapped[int | None]
    bed_length_ft: Mapped[float | None] = mapped_column(Numeric(4, 1))
    bed_width_ft: Mapped[float | None] = mapped_column(Numeric(4, 1))
    bed_height_ft: Mapped[float | None] = mapped_column(Numeric(4, 1))
    has_lift_gate: Mapped[bool] = mapped_column(default=False, server_default=text("false"))
    has_dolly: Mapped[bool] = mapped_column(default=False, server_default=text("false"))
    has_straps: Mapped[bool] = mapped_column(default=False, server_default=text("false"))
    has_blankets: Mapped[bool] = mapped_column(default=False, server_default=text("false"))
    is_default: Mapped[bool] = mapped_column(default=False, server_default=text("false"))
    status: Mapped[VehicleStatus] = mapped_column(
        Enum(VehicleStatus, name="vehiclestatus"),
        default=VehicleStatus.active,
        server_default=VehicleStatus.active.value,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
