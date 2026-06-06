import enum
import uuid
from datetime import date, datetime

from sqlalchemy import CHAR, Date, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.databases import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class IdentityVerificationKind(str, enum.Enum):
    drivers_license = "drivers_license"
    passport = "passport"
    business_doc = "business_doc"
    stripe_identity = "stripe_identity"
    insurance = "insurance"
    vehicle_registration = "vehicle_registration"


class IdentityVerificationStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    expired = "expired"


class IdentityVerification(Base):
    __tablename__ = "identity_verifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[IdentityVerificationKind] = mapped_column(
        Enum(IdentityVerificationKind, name="identityverificationkind"), nullable=False
    )
    status: Mapped[IdentityVerificationStatus] = mapped_column(
        Enum(IdentityVerificationStatus, name="identityverificationstatus"),
        default=IdentityVerificationStatus.pending,
        server_default=IdentityVerificationStatus.pending.value,
        nullable=False,
    )
    provider: Mapped[str | None] = mapped_column(String(64))
    provider_reference: Mapped[str | None] = mapped_column(String(128))
    document_url: Mapped[str | None] = mapped_column(String(1024))
    issuing_country: Mapped[str | None] = mapped_column(CHAR(2))
    issuing_state: Mapped[str | None] = mapped_column(String(32))
    expires_on: Mapped[date | None] = mapped_column(Date)
    reviewer_user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL")
    )
    review_notes: Mapped[str | None] = mapped_column(String(2048))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
