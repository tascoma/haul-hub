from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.user import VehicleType


class UserProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    full_name: str | None
    phone: str | None
    avatar_url: str | None
    shipper_enabled: bool
    hauler_enabled: bool
    stripe_account_id: str | None
    created_at: datetime
    updated_at: datetime


class UserProfileUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    avatar_url: str | None = None


class MeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    profile: UserProfileRead


class HaulerProfileCreate(BaseModel):
    vehicle_type: VehicleType
    vehicle_make: str | None = None
    vehicle_model: str | None = None
    vehicle_year: int | None = None
    max_weight_lbs: int | None = None
    max_length_ft: float | None = None
    max_width_ft: float | None = None
    max_height_ft: float | None = None
    license_number: str | None = None
    insurance_doc_url: str | None = None


class HaulerProfileUpdate(BaseModel):
    vehicle_type: VehicleType | None = None
    vehicle_make: str | None = None
    vehicle_model: str | None = None
    vehicle_year: int | None = None
    max_weight_lbs: int | None = None
    max_length_ft: float | None = None
    max_width_ft: float | None = None
    max_height_ft: float | None = None
    license_number: str | None = None
    insurance_doc_url: str | None = None


class HaulerProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    vehicle_type: VehicleType
    vehicle_make: str | None
    vehicle_model: str | None
    vehicle_year: int | None
    max_weight_lbs: int | None
    max_length_ft: float | None
    max_width_ft: float | None
    max_height_ft: float | None
    license_number: str | None
    insurance_doc_url: str | None
    verified_at: datetime | None
    created_at: datetime
    updated_at: datetime
