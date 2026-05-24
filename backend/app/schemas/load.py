from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.load import LoadStatus, Urgency


class LoadCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=4096)

    weight_lbs: int = Field(gt=0)
    length_ft: float | None = Field(default=None, gt=0)
    width_ft: float | None = Field(default=None, gt=0)
    height_ft: float | None = Field(default=None, gt=0)

    pickup_address: str = Field(min_length=1, max_length=255)
    pickup_city: str = Field(min_length=1, max_length=128)
    pickup_state: str = Field(min_length=2, max_length=32)
    pickup_zip: str = Field(min_length=3, max_length=16)
    pickup_window_start: datetime
    pickup_window_end: datetime

    dropoff_address: str = Field(min_length=1, max_length=255)
    dropoff_city: str = Field(min_length=1, max_length=128)
    dropoff_state: str = Field(min_length=2, max_length=32)
    dropoff_zip: str = Field(min_length=3, max_length=16)
    dropoff_by: datetime

    estimated_distance_miles: float = Field(gt=0)
    urgency: Urgency = Urgency.standard


class LoadUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=4096)
    weight_lbs: int | None = Field(default=None, gt=0)
    length_ft: float | None = Field(default=None, gt=0)
    width_ft: float | None = Field(default=None, gt=0)
    height_ft: float | None = Field(default=None, gt=0)
    pickup_address: str | None = None
    pickup_city: str | None = None
    pickup_state: str | None = None
    pickup_zip: str | None = None
    pickup_window_start: datetime | None = None
    pickup_window_end: datetime | None = None
    dropoff_address: str | None = None
    dropoff_city: str | None = None
    dropoff_state: str | None = None
    dropoff_zip: str | None = None
    dropoff_by: datetime | None = None
    estimated_distance_miles: float | None = Field(default=None, gt=0)
    urgency: Urgency | None = None


# Pricing-relevant fields that, when updated, require recalculating calculated_price_cents.
PRICE_RELEVANT_FIELDS = {"estimated_distance_miles", "weight_lbs", "urgency"}


class CancelRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=512)


class LoadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    shipper_id: str
    hauler_id: str | None

    title: str
    description: str | None
    photo_urls: list[str]

    weight_lbs: int
    length_ft: float | None
    width_ft: float | None
    height_ft: float | None

    pickup_address: str
    pickup_city: str
    pickup_state: str
    pickup_zip: str
    pickup_window_start: datetime
    pickup_window_end: datetime

    dropoff_address: str
    dropoff_city: str
    dropoff_state: str
    dropoff_zip: str
    dropoff_by: datetime

    estimated_distance_miles: float
    urgency: Urgency
    calculated_price_cents: int

    status: LoadStatus

    accepted_at: datetime | None
    picked_up_at: datetime | None
    delivered_at: datetime | None
    cancelled_at: datetime | None

    created_at: datetime
    updated_at: datetime
