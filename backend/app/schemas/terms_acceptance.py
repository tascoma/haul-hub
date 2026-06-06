from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.terms_acceptance import TermsDocumentKind


class TermsAcceptanceCreate(BaseModel):
    document_kind: TermsDocumentKind
    version: str


class TermsAcceptanceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    document_kind: TermsDocumentKind
    version: str
    accepted_at: datetime
    ip_address: str | None
    user_agent: str | None
    created_at: datetime
