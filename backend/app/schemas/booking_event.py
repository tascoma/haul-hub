from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.booking_event import BookingEventType


class BookingEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    load_id: str
    event_type: BookingEventType
    actor_user_id: str
    event_metadata: dict
    created_at: datetime
