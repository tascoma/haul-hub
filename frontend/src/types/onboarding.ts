export type Role = "customer" | "hauler";

export type OnboardingStep =
  | "profile"
  | "hauler_profile"
  | "hauler_vehicle"
  | "hauler_service_area"
  | "done";

export interface OnboardingChecks {
  has_vehicle: boolean;
  has_service_area: boolean;
}

export interface OnboardingStatus {
  profile_complete: boolean;
  customer_ready: boolean;
  hauler_ready: boolean;
  next_step: OnboardingStep;
  checks: OnboardingChecks;
}
