from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.databases import Base


class ProcessedWebhookEvent(Base):
    """One row per Stripe event id we have successfully processed.

    Stripe retries webhook deliveries, so the endpoint records each event id
    before dispatching its handler; a re-delivered event is recognised and
    skipped instead of being applied twice.
    """

    __tablename__ = "processed_webhook_events"

    event_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
