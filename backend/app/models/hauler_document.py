import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.databases import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class HaulerDocumentKind(str, enum.Enum):
    insurance_certificate = "insurance_certificate"
    vehicle_registration = "vehicle_registration"
    business_license = "business_license"
    dot_authority = "dot_authority"
    workers_comp = "workers_comp"
    other = "other"


class HaulerDocument(Base):
    __tablename__ = "hauler_documents"
    __table_args__ = (
        Index("ix_hauler_documents_user_kind_expiry", "hauler_user_id", "kind", "expires_on"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    hauler_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    vehicle_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("vehicles.id", ondelete="SET NULL")
    )
    kind: Mapped[HaulerDocumentKind] = mapped_column(
        Enum(HaulerDocumentKind, name="haulerdocumentkind"), nullable=False
    )
    document_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    policy_number: Mapped[str | None] = mapped_column(String(64))
    carrier_name: Mapped[str | None] = mapped_column(String(128))
    coverage_amount_cents: Mapped[int | None]
    effective_on: Mapped[date | None] = mapped_column(Date)
    expires_on: Mapped[date | None] = mapped_column(Date)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
