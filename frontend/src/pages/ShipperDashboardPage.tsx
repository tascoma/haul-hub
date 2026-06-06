import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { api, ApiError } from "../lib/api";
import type { Load } from "../lib/types";
import { formatPrice, formatStatus } from "../lib/format";

function LoadRow({ load }: { load: Load }) {
  return (
    <Link to={`/shipper/loads/${load.id}`} className="load-card">
      <div style={{ minWidth: 0, flex: 1 }}>
        <div style={{ display: "flex", gap: 6, marginBottom: 8, flexWrap: "wrap" }}>
          <span className={`hh-pill ${load.urgency === "express" ? "hh-pill--accent" : ""}`}>
            {load.urgency === "express" ? "EXPRESS" : "STANDARD"}
          </span>
          <span className={`status-pill status-${load.status}`}>{formatStatus(load.status)}</span>
        </div>
        <div className="title">{load.title}</div>
        <div className="hh-route" style={{ marginTop: 10, rowGap: 6 }}>
          <span className="hh-route__dot" />
          <div className="hh-route__where">
            {load.pickup_city}, {load.pickup_state}
          </div>
          <span className="hh-route__dot hh-route__dot--end" />
          <div className="hh-route__where">
            {load.dropoff_city}, {load.dropoff_state}
          </div>
        </div>
        <div className="meta" style={{ marginTop: 10 }}>
          {load.weight_lbs.toLocaleString()} lb · {load.estimated_distance_miles} mi
        </div>
      </div>
      <div style={{ textAlign: "right", flexShrink: 0 }}>
        <div className="price">{formatPrice(load.calculated_price_cents)}</div>
      </div>
    </Link>
  );
}

export function ShipperDashboardPage() {
  const { me } = useAuth();
  const [loads, setLoads] = useState<Load[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    api
      .get<Load[]>("/me/loads")
      .then((d) => active && setLoads(d))
      .catch((err) => active && setError(err instanceof ApiError ? err.detail : "Failed to load"))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, []);

  if (!me) return null;

  const total = loads.length;
  const inMotion = loads.filter((l) =>
    ["accepted", "picked_up", "in_transit"].includes(l.status),
  ).length;
  const delivered = loads.filter((l) => l.status === "delivered").length;
  const totalValue = loads.reduce((sum, l) => sum + l.calculated_price_cents, 0);

  return (
    <div>
      <div className="page-h">
        <div>
          <h1>Welcome back, {me.profile.full_name?.split(" ")[0] || me.email}</h1>
          <div className="sub">Post loads and track your shipments in one place.</div>
        </div>
        <Link
          to="/shipper/loads/new"
          className="accent btn-sm"
          style={{ height: 40, padding: "0 14px", display: "inline-flex", alignItems: "center", gap: 6 }}
        >
          <span style={{ fontSize: 18, lineHeight: 0 }}>+</span> Post a load
        </Link>
      </div>

      {error && <div className="error">{error}</div>}

      {!loading && (
        <div className="stat-strip" style={{ gridTemplateColumns: "repeat(4, 1fr)" }}>
          <div className="stat-card">
            <div className="l">Posted loads</div>
            <div className="v">{total}</div>
            <div className="sub">all time</div>
          </div>
          <div className="stat-card">
            <div className="l">In motion</div>
            <div className="v">{inMotion}</div>
            <div className="sub">accepted or en route</div>
          </div>
          <div className="stat-card">
            <div className="l">Delivered</div>
            <div className="v">{delivered}</div>
            <div className="sub">completed hauls</div>
          </div>
          <div className="stat-card">
            <div className="l">Total spend</div>
            <div className="v accent">{formatPrice(totalValue)}</div>
            <div className="sub">across all shipments</div>
          </div>
        </div>
      )}

      <div>
        <div className="section-h">
          <h3>My shipments</h3>
          {loads.length > 0 && (
            <Link to="/shipper/loads/new" className="hh-link">
              Post another
            </Link>
          )}
        </div>

        {loading && <div className="muted">Loading…</div>}

        {!loading && loads.length === 0 ? (
          <div className="empty">
            No loads yet.{" "}
            <Link to="/shipper/loads/new">Post your first load →</Link>
          </div>
        ) : (
          <div className="load-list">
            {loads.map((l) => (
              <LoadRow key={l.id} load={l} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
