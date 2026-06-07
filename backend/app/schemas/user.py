from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.user import BusinessType, UserStatus


class UserProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    full_name: str | None
    display_name: str | None
    phone: str | None
    avatar_url: str | None
    bio: str | None
    preferred_language: str
    timezone: str
    shipper_enabled: bool
    hauler_enabled: bool
    marketing_opt_in: bool
    stripe_customer_id: str | None
    stripe_connect_account_id: str | None
    address_line1: str | None
    address_city: str | None
    address_state: str | None
    address_zip: str | None
    billing_same_as_home: bool
    billing_address_line1: str | None
    billing_address_city: str | None
    billing_address_state: str | None
    billing_address_zip: str | None
    created_at: datetime
    updated_at: datetime


class UserProfileUpdate(BaseModel):
    full_name: str | None = None
    display_name: str | None = None
    phone: str | None = None
    avatar_url: str | None = None
    bio: str | None = None
    preferred_language: str | None = None
    timezone: str | None = None
    marketing_opt_in: bool | None = None
    address_line1: str | None = None
    address_city: str | None = None
    address_state: str | None = None
    address_zip: str | None = None
    billing_same_as_home: bool | None = None
    billing_address_line1: str | None = None
    billing_address_city: str | None = None
    billing_address_state: str | None = None
    billing_address_zip: str | None = None


class MeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    phone: str | None
    status: UserStatus
    email_verified_at: datetime | None
    phone_verified_at: datetime | None
    last_login_at: datetime | None
    profile: UserProfileRead


class HaulerProfileCreate(BaseModel):
    """Create the operational profile only. Vehicles are managed separately via /me/vehicles."""

    company_name: str | None = None
    business_type: BusinessType | None = None
    tax_id_last4: str | None = None
    years_experience: int | None = None
    bio: str | None = None
    service_radius_miles: int = 25
    accepts_disposal_jobs: bool = True
    accepts_donation_runs: bool = True
    accepts_hazardous: bool = False


class HaulerProfileUpdate(BaseModel):
    company_name: str | None = None
    business_type: BusinessType | None = None
    tax_id_last4: str | None = None
    years_experience: int | None = None
    bio: str | None = None
    home_base_address_id: str | None = None
    service_radius_miles: int | None = None
    accepts_disposal_jobs: bool | None = None
    accepts_donation_runs: bool | None = None
    accepts_hazardous: bool | None = None
    currently_available: bool | None = None
    auto_accept_under_cents: int | None = None


class HaulerProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    company_name: str | None
    business_type: BusinessType | None
    tax_id_last4: str | None
    years_experience: int | None
    bio: str | None
    home_base_address_id: str | None
    service_radius_miles: int
    accepts_disposal_jobs: bool
    accepts_donation_runs: bool
    accepts_hazardous: bool
    currently_available: bool
    auto_accept_under_cents: int | None
    rating_avg: float | None
    rating_count: int
    jobs_completed: int
    verified_at: datetime | None
    suspended_at: datetime | None
    created_at: datetime
    updated_at: datetime
