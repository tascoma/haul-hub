from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.hauler_document import HaulerDocumentKind


class HaulerDocumentCreate(BaseModel):
    kind: HaulerDocumentKind
    document_url: str
    vehicle_id: str | None = None
    policy_number: str | None = None
    carrier_name: str | None = None
    coverage_amount_cents: int | None = None
    effective_on: date | None = None
    expires_on: date | None = None


class HaulerDocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    hauler_user_id: str
    vehicle_id: str | None
    kind: HaulerDocumentKind
    document_url: str
    policy_number: str | None
    carrier_name: str | None
    coverage_amount_cents: int | None
    effective_on: date | None
    expires_on: date | None
    verified_at: datetime | None
    created_at: datetime
    updated_at: datetime
