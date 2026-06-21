export type Role = "customer" | "hauler";

export type OnboardingStep =
  | "profile"
  | "hauler_profile"
  | "hauler_vehicle"
  | "hauler_service_area"
  | "hauler_documents"
  | "hauler_verification"
  | "done";

export interface OnboardingChecks {
  has_vehicle: boolean;
  has_service_area: boolean;
  has_insurance: boolean;
  has_drivers_license: boolean;
  has_background_check: boolean;
}

export interface OnboardingStatus {
  profile_complete: boolean;
  customer_ready: boolean;
  hauler_ready: boolean;
  next_step: OnboardingStep;
  checks: OnboardingChecks;
}
