import type { ReactNode } from "react";
import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth";

function Logomark({ size = 28 }: { size?: number }) {
  const inner = Math.round(size * 0.6);
  return (
    <span className="app-brand-mark" style={{ width: size, height: size }}>
      <svg width={inner} height={inner} viewBox="0 0 24 24" fill="none" aria-hidden>
        <path
          d="M2 7h11v9H2zM13 11h5l3 3v2h-8z"
          stroke="var(--hh-accent)"
          strokeWidth="2.2"
          strokeLinejoin="round"
        />
        <circle cx="7" cy="17.5" r="1.6" stroke="var(--hh-accent)" strokeWidth="2" />
        <circle cx="17" cy="17.5" r="1.6" stroke="var(--hh-accent)" strokeWidth="2" />
      </svg>
    </span>
  );
}

interface NavItem {
  to: string;
  label: string;
  icon: ReactNode;
  badge?: string;
}

const ICONS = {
  home: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path d="M3 11l9-7 9 7v10h-6v-6h-6v6H3z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" />
    </svg>
  ),
  list: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path d="M4 6h16M4 12h16M4 18h16" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  ),
  plus: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path d="M12 5v14M5 12h14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  ),
  user: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden>
      <circle cx="12" cy="8" r="4" stroke="currentColor" strokeWidth="1.8" />
      <path d="M4 21c1-4 4-6 8-6s7 2 8 6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  ),
};

function initialsOf(value: string | null | undefined): string {
  if (!value) return "?";
  const parts = value.trim().split(/\s+/).slice(0, 2);
  return parts.map((p) => p[0]?.toUpperCase() ?? "").join("") || value[0]?.toUpperCase() || "?";
}

export function Layout({ children }: { children: ReactNode }) {
  const { me, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  // Auth pages get a centered shell, not the sidebar
  const isAuthRoute =
    location.pathname === "/login" || location.pathname === "/signup";
  if (!me || isAuthRoute) {
    return <div className="auth-shell">{children}</div>;
  }

  const navItems: NavItem[] = [{ to: "/dashboard", label: "Dashboard", icon: ICONS.home }];
  if (me.profile.hauler_enabled) {
    navItems.push({ to: "/loads", label: "Browse loads", icon: ICONS.list });
  }
  if (me.profile.shipper_enabled) {
    navItems.push({ to: "/loads/new", label: "Post a load", icon: ICONS.plus });
  }
  navItems.push({ to: "/profile", label: "Profile", icon: ICONS.user });

  const initials = initialsOf(me.profile.full_name || me.email);

  return (
    <div className="app-shell">
      <aside className="app-side">
        <Link to="/dashboard" className="app-brand">
          <Logomark size={28} />
          <span>Haul Hub</span>
        </Link>

        <nav className="app-nav-list">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/dashboard"}
              className={({ isActive }) =>
                isActive ? "app-nav-item active" : "app-nav-item"
              }
            >
              {item.icon}
              <span style={{ flex: 1 }}>{item.label}</span>
              {item.badge && <span className="app-nav-item-badge">{item.badge}</span>}
            </NavLink>
          ))}
        </nav>

        <div className="app-side-spacer" />

        <div className="app-side-user">
          <span className="hh-avatar hh-avatar--sm hh-avatar--dark">{initials}</span>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div className="app-side-user-name">{me.profile.full_name || "Member"}</div>
            <div className="app-side-user-mail">{me.email}</div>
          </div>
          <button type="button" className="link-button" onClick={handleLogout}>
            Log out
          </button>
        </div>
      </aside>

      <main className="app-main">{children}</main>
    </div>
  );
}
