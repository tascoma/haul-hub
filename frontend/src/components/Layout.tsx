import type { ReactNode } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth";

export function Layout({ children }: { children: ReactNode }) {
  const { me, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="app-shell">
      <header className="app-nav">
        <Link to="/" className="brand">
          Haul Hub
        </Link>

        {me ? (
          <nav className="nav-links">
            <NavLink to="/dashboard">Dashboard</NavLink>
            {me.profile.shipper_enabled && <NavLink to="/loads/new">Post a load</NavLink>}
            {me.profile.hauler_enabled && <NavLink to="/loads">Browse loads</NavLink>}
            <NavLink to="/profile">Profile</NavLink>
            <span className="nav-email">{me.email}</span>
            <button type="button" className="link-button" onClick={handleLogout}>
              Log out
            </button>
          </nav>
        ) : (
          <nav className="nav-links">
            <NavLink to="/login">Log in</NavLink>
            <NavLink to="/signup">Sign up</NavLink>
          </nav>
        )}
      </header>
      <main className="app-main">{children}</main>
    </div>
  );
}
