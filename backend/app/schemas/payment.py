from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.payment import PaymentStatus


class ConnectOnboardingResponse(BaseModel):
    url: str


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    load_id: str
    amount_cents: int
    platform_fee_cents: int
    hauler_payout_cents: int
    status: PaymentStatus
    stripe_payment_intent_id: str | None
    stripe_transfer_id: str | None
    authorized_at: datetime | None
    captured_at: datetime | None
    transferred_at: datetime | None
    refunded_at: datetime | None
    created_at: datetime
    updated_at: datetime
