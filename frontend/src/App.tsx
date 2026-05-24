import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { BrowseLoadsPage } from "./pages/BrowseLoadsPage";
import { DashboardPage } from "./pages/DashboardPage";
import { LoadDetailPage } from "./pages/LoadDetailPage";
import { LoginPage } from "./pages/LoginPage";
import { PostLoadPage } from "./pages/PostLoadPage";
import { ProfilePage } from "./pages/ProfilePage";
import { SignupPage } from "./pages/SignupPage";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <ProfilePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/loads"
          element={
            <ProtectedRoute>
              <BrowseLoadsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/loads/new"
          element={
            <ProtectedRoute>
              <PostLoadPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/loads/:id"
          element={
            <ProtectedRoute>
              <LoadDetailPage />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<div className="muted">Page not found.</div>} />
      </Routes>
    </Layout>
  );
}
