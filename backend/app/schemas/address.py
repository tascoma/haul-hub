from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.address import AddressTypeHint


class AddressBase(BaseModel):
    line1: str
    line2: str | None = None
    city: str
    state: str
    postal_code: str
    country: str = "US"
    lat: Decimal | None = None
    lng: Decimal | None = None
    place_id: str | None = None
    address_type_hint: AddressTypeHint | None = None
    gate_code: str | None = None
    access_notes: str | None = None


class AddressCreate(AddressBase):
    pass


class AddressUpdate(BaseModel):
    line1: str | None = None
    line2: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = None
    lat: Decimal | None = None
    lng: Decimal | None = None
    place_id: str | None = None
    address_type_hint: AddressTypeHint | None = None
    gate_code: str | None = None
    access_notes: str | None = None


class AddressRead(AddressBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime

    @field_validator("lat", "lng", mode="before")
    @classmethod
    def _normalize_decimals(cls, v: object) -> object:
        # Allow PostGIS Numeric values to round-trip cleanly.
        return v


class SavedAddressCreate(BaseModel):
    address_id: str
    label: str
    is_default_pickup: bool = False
    is_default_dropoff: bool = False


class SavedAddressUpdate(BaseModel):
    label: str | None = None
    is_default_pickup: bool | None = None
    is_default_dropoff: bool | None = None


class SavedAddressRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    address_id: str
    label: str
    is_default_pickup: bool
    is_default_dropoff: bool
    address: AddressRead
    created_at: datetime
    updated_at: datetime
