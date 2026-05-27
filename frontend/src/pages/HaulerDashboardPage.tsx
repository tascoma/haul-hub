import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { api, ApiError } from "../lib/api";
import type { Load } from "../lib/types";
import { formatPrice, formatStatus } from "../lib/format";

const HAULER_PAYOUT_RATE = 0.85;

function HaulRow({ load }: { load: Load }) {
  return (
    <Link to={`/hauler/loads/${load.id}`} className="load-card">
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
        <div className="price">{formatPrice(Math.round(load.calculated_price_cents * HAULER_PAYOUT_RATE))}</div>
        <div className="meta" style={{ marginTop: 4 }}>your payout</div>
      </div>
    </Link>
  );
}

export function HaulerDashboardPage() {
  const { me } = useAuth();
  const [hauls, setHauls] = useState<Load[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    api
      .get<Load[]>("/me/hauls")
      .then((d) => active && setHauls(d))
      .catch((err) => active && setError(err instanceof ApiError ? err.detail : "Failed to load"))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, []);

  if (!me) return null;

  const total = hauls.length;
  const inMotion = hauls.filter((l) =>
    ["accepted", "picked_up", "in_transit"].includes(l.status),
  ).length;
  const delivered = hauls.filter((l) => l.status === "delivered").length;
  const totalEarnings = hauls.reduce(
    (sum, l) => sum + Math.round(l.calculated_price_cents * HAULER_PAYOUT_RATE),
    0,
  );

  return (
    <div>
      <div className="page-h">
        <div>
          <h1>Welcome back, {me.profile.full_name?.split(" ")[0] || me.email}</h1>
          <div className="sub">Claim loads near you and track your active hauls.</div>
        </div>
        <Link
          to="/hauler/loads"
          className="primary btn-sm"
          style={{ height: 40, padding: "0 14px", display: "inline-flex", alignItems: "center", gap: 6 }}
        >
          Find loads
        </Link>
      </div>

      {error && <div className="error">{error}</div>}

      {!loading && (
        <div className="stat-strip" style={{ gridTemplateColumns: "repeat(4, 1fr)" }}>
          <div className="stat-card">
            <div className="l">Total hauls</div>
            <div className="v">{total}</div>
            <div className="sub">all time</div>
          </div>
          <div className="stat-card">
            <div className="l">In motion</div>
            <div className="v">{inMotion}</div>
            <div className="sub">active right now</div>
          </div>
          <div className="stat-card">
            <div className="l">Delivered</div>
            <div className="v">{delivered}</div>
            <div className="sub">completed</div>
          </div>
          <div className="stat-card">
            <div className="l">Total earnings</div>
            <div className="v accent">{formatPrice(totalEarnings)}</div>
            <div className="sub">at 85% payout rate</div>
          </div>
        </div>
      )}

      <div>
        <div className="section-h">
          <h3>My hauls</h3>
          <Link to="/hauler/loads" className="hh-link">
            Find more
          </Link>
        </div>

        {loading && <div className="muted">Loading…</div>}

        {!loading && hauls.length === 0 ? (
          <div className="empty">
            No hauls yet. <Link to="/hauler/loads">Browse available loads →</Link>
          </div>
        ) : (
          <div className="load-list">
            {hauls.map((l) => (
              <HaulRow key={l.id} load={l} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
