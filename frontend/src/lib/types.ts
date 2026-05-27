// Mirrors backend/app/schemas — keep in sync when adding fields.

export type VehicleType =
  | "pickup"
  | "pickup_with_trailer"
  | "flatbed"
  | "box_truck"
  | "cargo_van"
  | "semi"
  | "dump_truck"
  | "roll_off"
  | "other";

export type VehicleStatus = "active" | "inactive" | "retired";

export interface Vehicle {
  id: string;
  owner_user_id: string;
  nickname: string | null;
  vehicle_type: VehicleType;
  make: string | null;
  model: string | null;
  year: number | null;
  color: string | null;
  license_plate: string | null;
  license_plate_state: string | null;
  vin: string | null;
  max_payload_lbs: number | null;
  max_volume_cuft: number | null;
  bed_length_ft: number | null;
  bed_width_ft: number | null;
  bed_height_ft: number | null;
  has_lift_gate: boolean;
  has_dolly: boolean;
  has_straps: boolean;
  has_blankets: boolean;
  is_default: boolean;
  status: VehicleStatus;
  created_at: string;
  updated_at: string;
}

export type Urgency = "standard" | "express";

export type LoadStatus =
  | "draft"
  | "posted"
  | "accepted"
  | "picked_up"
  | "in_transit"
  | "delivered"
  | "cancelled";

export type PaymentStatus =
  | "pending"
  | "authorized"
  | "captured"
  | "transferred"
  | "refunded"
  | "failed";

export type BusinessType = "individual" | "llc" | "corporation" | "partnership";
export type UserStatus = "active" | "suspended" | "deleted";

export interface UserProfile {
  user_id: string;
  full_name: string | null;
  display_name: string | null;
  phone: string | null;
  avatar_url: string | null;
  bio: string | null;
  preferred_language: string;
  timezone: string;
  shipper_enabled: boolean;
  hauler_enabled: boolean;
  marketing_opt_in: boolean;
  stripe_customer_id: string | null;
  stripe_connect_account_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface HaulerProfile {
  user_id: string;
  company_name: string | null;
  business_type: BusinessType | null;
  tax_id_last4: string | null;
  years_experience: number | null;
  bio: string | null;
  home_base_address_id: string | null;
  service_radius_miles: number;
  accepts_disposal_jobs: boolean;
  accepts_donation_runs: boolean;
  accepts_hazardous: boolean;
  currently_available: boolean;
  auto_accept_under_cents: number | null;
  rating_avg: number | null;
  rating_count: number;
  jobs_completed: number;
  verified_at: string | null;
  suspended_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface Me {
  id: string;
  email: string;
  phone: string | null;
  status: UserStatus;
  email_verified_at: string | null;
  phone_verified_at: string | null;
  last_login_at: string | null;
  profile: UserProfile;
}

export interface Load {
  id: string;
  shipper_id: string;
  hauler_id: string | null;
  title: string;
  description: string | null;
  photo_urls: string[];
  weight_lbs: number;
  length_ft: number | null;
  width_ft: number | null;
  height_ft: number | null;
  pickup_address: string;
  pickup_city: string;
  pickup_state: string;
  pickup_zip: string;
  pickup_window_start: string;
  pickup_window_end: string;
  dropoff_address: string;
  dropoff_city: string;
  dropoff_state: string;
  dropoff_zip: string;
  dropoff_by: string;
  estimated_distance_miles: number;
  urgency: Urgency;
  calculated_price_cents: number;
  status: LoadStatus;
  accepted_at: string | null;
  picked_up_at: string | null;
  delivered_at: string | null;
  cancelled_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface LoadCreate {
  title: string;
  description?: string | null;
  weight_lbs: number;
  length_ft?: number | null;
  width_ft?: number | null;
  height_ft?: number | null;
  pickup_address: string;
  pickup_city: string;
  pickup_state: string;
  pickup_zip: string;
  pickup_window_start: string;
  pickup_window_end: string;
  dropoff_address: string;
  dropoff_city: string;
  dropoff_state: string;
  dropoff_zip: string;
  dropoff_by: string;
  estimated_distance_miles: number;
  urgency: Urgency;
}

export interface Payment {
  id: string;
  load_id: string;
  amount_cents: number;
  platform_fee_cents: number;
  hauler_payout_cents: number;
  status: PaymentStatus;
  stripe_payment_intent_id: string | null;
  stripe_transfer_id: string | null;
  authorized_at: string | null;
  captured_at: string | null;
  transferred_at: string | null;
  refunded_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}
