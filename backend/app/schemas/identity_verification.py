from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.identity_verification import (
    IdentityVerificationKind,
    IdentityVerificationStatus,
)


class IdentityVerificationCreate(BaseModel):
    kind: IdentityVerificationKind
    provider: str | None = None
    provider_reference: str | None = None
    document_url: str | None = None
    issuing_country: str | None = None
    issuing_state: str | None = None
    expires_on: date | None = None


class IdentityVerificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    kind: IdentityVerificationKind
    status: IdentityVerificationStatus
    provider: str | None
    provider_reference: str | None
    document_url: str | None
    issuing_country: str | None
    issuing_state: str | None
    expires_on: date | None
    submitted_at: datetime | None
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime
