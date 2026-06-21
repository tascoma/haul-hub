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
  truck: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path d="M2 7h11v9H2zM13 11h5l3 3v2h-8z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" />
      <circle cx="7" cy="17.5" r="1.5" stroke="currentColor" strokeWidth="1.8" />
      <circle cx="17" cy="17.5" r="1.5" stroke="currentColor" strokeWidth="1.8" />
    </svg>
  ),
  card: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden>
      <rect x="2" y="5" width="20" height="14" rx="2" stroke="currentColor" strokeWidth="1.8" />
      <path d="M2 10h20" stroke="currentColor" strokeWidth="1.8" />
    </svg>
  ),
};

const SHIPPER_NAV: NavItem[] = [
  { to: "/shipper/dashboard", label: "Dashboard", icon: ICONS.home },
  { to: "/shipper/loads/new", label: "Post a load", icon: ICONS.plus },
  { to: "/payment-method", label: "Payment", icon: ICONS.card },
  { to: "/profile", label: "Profile", icon: ICONS.user },
];

const HAULER_NAV: NavItem[] = [
  { to: "/hauler/dashboard", label: "Dashboard", icon: ICONS.home },
  { to: "/hauler/loads", label: "Find loads", icon: ICONS.list },
  { to: "/hauler/hauls", label: "My hauls", icon: ICONS.truck },
  { to: "/profile", label: "Profile", icon: ICONS.user },
];

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

  const isLandingRoute = location.pathname === "/";
  if (isLandingRoute) return <>{children}</>;

  const isAuthRoute = location.pathname === "/login" || location.pathname === "/signup";
  const isOnboardingRoute = location.pathname.startsWith("/onboarding");
  if (!me || isAuthRoute || isOnboardingRoute) {
    return <div className="auth-shell">{children}</div>;
  }

  const isHaulerRoute =
    location.pathname.startsWith("/hauler") ||
    (!location.pathname.startsWith("/shipper") && me.profile.hauler_enabled && !me.profile.shipper_enabled);

  const navItems = isHaulerRoute ? HAULER_NAV : SHIPPER_NAV;
  const hasBothRoles = me.profile.shipper_enabled && me.profile.hauler_enabled;

  const activeItem = navItems.find(
    (item) =>
      location.pathname === item.to ||
      (item.to !== "/profile" && location.pathname.startsWith(item.to + "/")),
  );
  const pageTitle = activeItem?.label ?? "Haul Hub";

  const initials = initialsOf(me.profile.full_name || me.email);

  return (
    <div className="app-shell">
      <aside className="app-side">
        <Link
          to={isHaulerRoute ? "/hauler/dashboard" : "/shipper/dashboard"}
          className="app-brand"
        >
          <Logomark size={28} />
          <span>Haul Hub</span>
        </Link>

        {hasBothRoles && (
          <div className="app-role-switcher">
            <Link
              to="/shipper/dashboard"
              className={`app-role-btn${!isHaulerRoute ? " active" : ""}`}
            >
              Shipper
            </Link>
            <Link
              to="/hauler/dashboard"
              className={`app-role-btn${isHaulerRoute ? " active" : ""}`}
            >
              Hauler
            </Link>
          </div>
        )}

        <nav className="app-nav-list">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to.endsWith("/dashboard")}
              className={({ isActive }) => (isActive ? "app-nav-item active" : "app-nav-item")}
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
            <div className="app-side-user-mail" style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{me.email}</div>
            <button type="button" className="link-button app-side-user-logout" onClick={handleLogout}>
              Log out
            </button>
          </div>
        </div>
      </aside>

      <div className="app-right">
        <header className="app-header">
          <span className="app-header-title">{pageTitle}</span>
          <div className="app-header-meta">
            {isHaulerRoute ? (
              <span className="hh-pill hh-pill--solid">Hauler</span>
            ) : (
              <span className="hh-pill hh-pill--accent">Shipper</span>
            )}
          </div>
        </header>
        <main className="app-main">{children}</main>
      </div>
    </div>
  );
}
