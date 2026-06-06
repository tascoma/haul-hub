import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { useOnboardingStatus } from "../hooks/useOnboardingStatus";

/**
 * Wrap protected pages that require finished onboarding. If the user still
 * has steps left (`next_step !== "done"`), bounces them to /onboarding.
 */
export function OnboardingGate({ children }: { children: ReactNode }) {
  const { status, loading } = useOnboardingStatus();

  if (loading) return <div className="page-loading">Loading…</div>;
  if (status && status.next_step !== "done") {
    return <Navigate to="/onboarding" replace />;
  }
  return <>{children}</>;
}
