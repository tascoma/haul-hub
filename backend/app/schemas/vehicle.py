from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.user import VehicleType
from app.models.vehicle import VehicleStatus


class VehicleBase(BaseModel):
    nickname: str | None = None
    vehicle_type: VehicleType
    make: str | None = None
    model: str | None = None
    year: int | None = None
    color: str | None = None
    license_plate: str | None = None
    license_plate_state: str | None = None
    vin: str | None = None
    max_payload_lbs: int | None = None
    max_volume_cuft: int | None = None
    bed_length_ft: Decimal | None = None
    bed_width_ft: Decimal | None = None
    bed_height_ft: Decimal | None = None
    has_lift_gate: bool = False
    has_dolly: bool = False
    has_straps: bool = False
    has_blankets: bool = False
    is_default: bool = False


class VehicleCreate(VehicleBase):
    pass


class VehicleUpdate(BaseModel):
    nickname: str | None = None
    vehicle_type: VehicleType | None = None
    make: str | None = None
    model: str | None = None
    year: int | None = None
    color: str | None = None
    license_plate: str | None = None
    license_plate_state: str | None = None
    vin: str | None = None
    max_payload_lbs: int | None = None
    max_volume_cuft: int | None = None
    bed_length_ft: Decimal | None = None
    bed_width_ft: Decimal | None = None
    bed_height_ft: Decimal | None = None
    has_lift_gate: bool | None = None
    has_dolly: bool | None = None
    has_straps: bool | None = None
    has_blankets: bool | None = None
    is_default: bool | None = None
    status: VehicleStatus | None = None


class VehicleRead(VehicleBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    owner_user_id: str
    status: VehicleStatus
    created_at: datetime
    updated_at: datetime
