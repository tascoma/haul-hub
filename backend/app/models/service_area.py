import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.databases import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class ServiceAreaKind(str, enum.Enum):
    radius = "radius"
    postal_code = "postal_code"
    polygon = "polygon"


class ServiceArea(Base):
    """Where a hauler operates.

    `polygon geography(Polygon, 4326)` is a Postgres-only column (added by
    migration 0014) and intentionally not mapped on the ORM model.
    """

    __tablename__ = "service_areas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    hauler_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[ServiceAreaKind] = mapped_column(
        Enum(ServiceAreaKind, name="serviceareakind"), nullable=False
    )
    center_address_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("addresses.id", ondelete="SET NULL")
    )
    radius_miles: Mapped[int | None]
    postal_code: Mapped[str | None] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
