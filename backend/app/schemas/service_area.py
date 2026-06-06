from datetime import datetime

from pydantic import BaseModel, ConfigDict, model_validator

from app.models.service_area import ServiceAreaKind


class ServiceAreaCreate(BaseModel):
    kind: ServiceAreaKind
    center_address_id: str | None = None
    radius_miles: int | None = None
    postal_code: str | None = None

    @model_validator(mode="after")
    def _check_kind_fields(self) -> "ServiceAreaCreate":
        if self.kind == ServiceAreaKind.radius and (
            not self.center_address_id or self.radius_miles is None
        ):
            raise ValueError(
                "kind='radius' requires center_address_id and radius_miles"
            )
        if self.kind == ServiceAreaKind.postal_code and not self.postal_code:
            raise ValueError("kind='postal_code' requires postal_code")
        return self


class ServiceAreaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    hauler_user_id: str
    kind: ServiceAreaKind
    center_address_id: str | None
    radius_miles: int | None
    postal_code: str | None
    created_at: datetime
    updated_at: datetime
