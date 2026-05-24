// Mirrors backend/app/schemas — keep in sync when adding fields.

export type VehicleType =
  | "pickup"
  | "pickup_with_trailer"
  | "flatbed"
  | "box_truck"
  | "cargo_van"
  | "semi"
  | "other";

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

export interface UserProfile {
  user_id: string;
  full_name: string | null;
  phone: string | null;
  avatar_url: string | null;
  shipper_enabled: boolean;
  hauler_enabled: boolean;
  stripe_account_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface HaulerProfile {
  user_id: string;
  vehicle_type: VehicleType;
  vehicle_make: string | null;
  vehicle_model: string | null;
  vehicle_year: number | null;
  max_weight_lbs: number | null;
  max_length_ft: number | null;
  max_width_ft: number | null;
  max_height_ft: number | null;
  license_number: string | null;
  insurance_doc_url: string | null;
  verified_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface Me {
  id: string;
  email: string;
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
