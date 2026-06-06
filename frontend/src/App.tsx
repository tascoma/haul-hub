import type { ReactNode } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { OnboardingGate } from "./components/OnboardingGate";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { useAuth } from "./lib/auth";
import { BrowseLoadsPage } from "./pages/BrowseLoadsPage";
import { HaulerDashboardPage } from "./pages/HaulerDashboardPage";
import { LandingPage } from "./pages/LandingPage";
import { LoadDetailPage } from "./pages/LoadDetailPage";
import { LoginPage } from "./pages/LoginPage";
import { PostLoadPage } from "./pages/PostLoadPage";
import { ProfilePage } from "./pages/ProfilePage";
import { ShipperDashboardPage } from "./pages/ShipperDashboardPage";
import { SignupPage } from "./pages/SignupPage";
import { HaulerProfileOnboardingPage } from "./pages/onboarding/HaulerProfileOnboardingPage";
import { OnboardingRouterPage } from "./pages/onboarding/OnboardingRouterPage";
import { ProfileOnboardingPage } from "./pages/onboarding/ProfileOnboardingPage";
import { ServiceAreaOnboardingPage } from "./pages/onboarding/ServiceAreaOnboardingPage";
import { StripeRefreshPage } from "./pages/onboarding/StripeRefreshPage";
import { StripeReturnPage } from "./pages/onboarding/StripeReturnPage";
import { VehicleOnboardingPage } from "./pages/onboarding/VehicleOnboardingPage";
import { PaymentMethodPage } from "./pages/PaymentMethodPage";

function ShipperRoute({ children }: { children: ReactNode }) {
  const { me } = useAuth();
  if (!me) return null;
  if (!me.profile.shipper_enabled) return <Navigate to="/hauler/dashboard" replace />;
  return <>{children}</>;
}

function HaulerRoute({ children }: { children: ReactNode }) {
  const { me } = useAuth();
  if (!me) return null;
  if (!me.profile.hauler_enabled) return <Navigate to="/shipper/dashboard" replace />;
  return <>{children}</>;
}

function DashboardRedirect() {
  const { me } = useAuth();
  if (!me) return null;
  if (me.profile.hauler_enabled && !me.profile.shipper_enabled) {
    return <Navigate to="/hauler/dashboard" replace />;
  }
  return <Navigate to="/shipper/dashboard" replace />;
}

export default function App() {
  return (
    <Layout>
      <Routes>
        {/* Public */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />

        {/* Onboarding (auth required, no sidebar) */}
        <Route
          path="/onboarding"
          element={<ProtectedRoute><OnboardingRouterPage /></ProtectedRoute>}
        />
        <Route
          path="/onboarding/profile"
          element={<ProtectedRoute><ProfileOnboardingPage /></ProtectedRoute>}
        />
        <Route
          path="/onboarding/hauler/profile"
          element={<ProtectedRoute><HaulerProfileOnboardingPage /></ProtectedRoute>}
        />
        <Route
          path="/onboarding/hauler/vehicle"
          element={<ProtectedRoute><VehicleOnboardingPage /></ProtectedRoute>}
        />
        <Route
          path="/onboarding/hauler/service-area"
          element={<ProtectedRoute><ServiceAreaOnboardingPage /></ProtectedRoute>}
        />
        <Route
          path="/onboarding/stripe/return"
          element={<ProtectedRoute><StripeReturnPage /></ProtectedRoute>}
        />
        <Route
          path="/onboarding/stripe/refresh"
          element={<ProtectedRoute><StripeRefreshPage /></ProtectedRoute>}
        />

        {/* Legacy redirect */}
        <Route
          path="/dashboard"
          element={<ProtectedRoute><OnboardingGate><DashboardRedirect /></OnboardingGate></ProtectedRoute>}
        />

        {/* Shared */}
        <Route
          path="/profile"
          element={<ProtectedRoute><OnboardingGate><ProfilePage /></OnboardingGate></ProtectedRoute>}
        />
        <Route
          path="/payment-method"
          element={<ProtectedRoute><OnboardingGate><PaymentMethodPage /></OnboardingGate></ProtectedRoute>}
        />

        {/* ── Shipper UI ── */}
        <Route
          path="/shipper/dashboard"
          element={
            <ProtectedRoute>
              <OnboardingGate>
                <ShipperRoute>
                  <ShipperDashboardPage />
                </ShipperRoute>
              </OnboardingGate>
            </ProtectedRoute>
          }
        />
        <Route
          path="/shipper/loads/new"
          element={
            <ProtectedRoute>
              <OnboardingGate>
                <ShipperRoute>
                  <PostLoadPage />
                </ShipperRoute>
              </OnboardingGate>
            </ProtectedRoute>
          }
        />
        <Route
          path="/shipper/loads/:id"
          element={
            <ProtectedRoute>
              <OnboardingGate>
                <ShipperRoute>
                  <LoadDetailPage />
                </ShipperRoute>
              </OnboardingGate>
            </ProtectedRoute>
          }
        />

        {/* ── Hauler UI ── */}
        <Route
          path="/hauler/dashboard"
          element={
            <ProtectedRoute>
              <OnboardingGate>
                <HaulerRoute>
                  <HaulerDashboardPage />
                </HaulerRoute>
              </OnboardingGate>
            </ProtectedRoute>
          }
        />
        <Route
          path="/hauler/loads"
          element={
            <ProtectedRoute>
              <OnboardingGate>
                <HaulerRoute>
                  <BrowseLoadsPage />
                </HaulerRoute>
              </OnboardingGate>
            </ProtectedRoute>
          }
        />
        <Route
          path="/hauler/hauls"
          element={
            <ProtectedRoute>
              <OnboardingGate>
                <HaulerRoute>
                  <HaulerDashboardPage />
                </HaulerRoute>
              </OnboardingGate>
            </ProtectedRoute>
          }
        />
        <Route
          path="/hauler/loads/:id"
          element={
            <ProtectedRoute>
              <OnboardingGate>
                <HaulerRoute>
                  <LoadDetailPage />
                </HaulerRoute>
              </OnboardingGate>
            </ProtectedRoute>
          }
        />

        <Route path="*" element={<div className="muted">Page not found.</div>} />
      </Routes>
    </Layout>
  );
}
