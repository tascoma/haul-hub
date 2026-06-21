import { Navigate } from "react-router-dom";
import { useAuth } from "../../lib/auth";
import { useOnboardingStatus } from "../../hooks/useOnboardingStatus";

const ONBOARDING_PATHS = {
  profile: "/onboarding/profile",
  hauler_profile: "/onboarding/hauler/profile",
  hauler_vehicle: "/onboarding/hauler/vehicle",
  hauler_service_area: "/onboarding/hauler/service-area",
  hauler_documents: "/onboarding/hauler/documents",
  hauler_verification: "/onboarding/hauler/verification",
} as const;

export function OnboardingRouterPage() {
  const { me } = useAuth();
  const { status, loading, error } = useOnboardingStatus();

  if (loading) return <div className="page-loading">Loading…</div>;
  if (error) return <div className="error">{error}</div>;
  if (!status || !me) return null;

  if (status.next_step === "done") {
    const dest =
      me.profile.hauler_enabled && !me.profile.shipper_enabled
        ? "/hauler/dashboard"
        : "/shipper/dashboard";
    return <Navigate to={dest} replace />;
  }

  return <Navigate to={ONBOARDING_PATHS[status.next_step]} replace />;
}
