import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.databases import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class PaymentStatus(str, enum.Enum):
    pending = "pending"  # row created, no Stripe interaction yet
    authorized = "authorized"  # PaymentIntent created with manual capture
    captured = "captured"  # funds captured into platform balance
    transferred = "transferred"  # paid out to hauler's Connect account
    refunded = "refunded"  # cancel-after-accept refund
    failed = "failed"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    load_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("loads.id", ondelete="CASCADE"), index=True, nullable=False
    )

    stripe_payment_intent_id: Mapped[str | None] = mapped_column(String(128))
    stripe_transfer_id: Mapped[str | None] = mapped_column(String(128))

    amount_cents: Mapped[int] = mapped_column(nullable=False)
    platform_fee_cents: Mapped[int] = mapped_column(nullable=False)
    hauler_payout_cents: Mapped[int] = mapped_column(nullable=False)

    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus),
        default=PaymentStatus.pending,
        server_default=PaymentStatus.pending.value,
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(String(1024))

    authorized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    transferred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
