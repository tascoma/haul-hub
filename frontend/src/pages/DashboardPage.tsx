import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { api, ApiError } from "../lib/api";
import type { Load } from "../lib/types";
import { formatPrice, formatStatus } from "../lib/format";

function LoadRow({ load }: { load: Load }) {
  return (
    <Link to={`/loads/${load.id}`} className="load-card">
      <div style={{ minWidth: 0, flex: 1 }}>
        <div style={{ display: "flex", gap: 6, marginBottom: 8, flexWrap: "wrap" }}>
          <span
            className={`hh-pill ${load.urgency === "express" ? "hh-pill--accent" : ""}`}
          >
            {load.urgency === "express" ? "EXPRESS" : "STANDARD"}
          </span>
          <span className={`status-pill status-${load.status}`}>
            {formatStatus(load.status)}
          </span>
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

function statsFor(loads: Load[]) {
  const total = loads.length;
  const inMotion = loads.filter((l) =>
    ["accepted", "picked_up", "in_transit"].includes(l.status),
  ).length;
  const value = loads.reduce((sum, l) => sum + l.calculated_price_cents, 0);
  const delivered = loads.filter((l) => l.status === "delivered").length;
  return { total, inMotion, value, delivered };
}

export function DashboardPage() {
  const { me } = useAuth();
  const [myLoads, setMyLoads] = useState<Load[]>([]);
  const [myHauls, setMyHauls] = useState<Load[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!me) return;
    let active = true;
    setLoading(true);
    const reqs = [
      api.get<Load[]>("/me/loads").then((d) => active && setMyLoads(d)),
    ];
    if (me.profile.hauler_enabled) {
      reqs.push(api.get<Load[]>("/me/hauls").then((d) => active && setMyHauls(d)));
    }
    Promise.all(reqs)
      .catch((err) => active && setError(err instanceof ApiError ? err.detail : "Failed to load"))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [me]);

  if (!me) return null;

  const bothRoles = me.profile.shipper_enabled && me.profile.hauler_enabled;
  const shipperStats = statsFor(myLoads);
  const haulerStats = statsFor(myHauls);

  return (
    <div>
      <div className="page-h">
        <div>
          <h1>Welcome back, {me.profile.full_name?.split(" ")[0] || me.email}</h1>
          <div className="sub">
            {me.profile.shipper_enabled && me.profile.hauler_enabled
              ? "Your shipments and hauls in one place."
              : me.profile.hauler_enabled
                ? "Hauler dashboard · claim a load to get moving."
                : "Post a load and we'll match you with a hauler in minutes."}
          </div>
        </div>
        {me.profile.shipper_enabled && (
          <Link to="/loads/new" className="accent btn-sm" style={{ height: 40, padding: "0 14px" }}>
            <span style={{ fontSize: 18, lineHeight: 0 }}>+</span> Post a load
          </Link>
        )}
      </div>

      {!me.profile.hauler_enabled && (
        <div className="card" style={{ display: "flex", gap: 14, alignItems: "center" }}>
          <div
            style={{
              width: 44,
              height: 44,
              borderRadius: 12,
              background: "var(--hh-accent-soft)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
              <path
                d="M2 7h11v9H2zM13 11h5l3 3v2h-8z"
                stroke="var(--hh-accent-text)"
                strokeWidth="1.8"
                strokeLinejoin="round"
              />
              <circle cx="7" cy="17.5" r="1.7" stroke="var(--hh-accent-text)" strokeWidth="1.8" />
              <circle cx="17" cy="17.5" r="1.7" stroke="var(--hh-accent-text)" strokeWidth="1.8" />
            </svg>
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 700, font: "700 14px var(--hh-font-display)" }}>
              Want to haul loads too?
            </div>
            <div className="muted" style={{ fontSize: 13, marginTop: 4 }}>
              Enable your hauler role to start claiming loads near you.
            </div>
          </div>
          <Link to="/profile" className="outline btn-sm">
            Enable hauler
          </Link>
        </div>
      )}

      {error && <div className="error">{error}</div>}
      {loading && <div className="muted">Loading…</div>}

      {!loading && (
        <div className="stat-strip">
          {me.profile.shipper_enabled && (
            <>
              <div className="stat-card">
                <div className="l">Posted loads</div>
                <div className="v">{shipperStats.total}</div>
                <div className="sub">
                  {shipperStats.inMotion} in motion · {shipperStats.delivered} delivered
                </div>
              </div>
              <div className="stat-card">
                <div className="l">Total value</div>
                <div className="v accent">{formatPrice(shipperStats.value)}</div>
                <div className="sub">across your shipments</div>
              </div>
            </>
          )}
          {me.profile.hauler_enabled && (
            <>
              <div className="stat-card">
                <div className="l">Active hauls</div>
                <div className="v">{haulerStats.total}</div>
                <div className="sub">
                  {haulerStats.inMotion} in motion · {haulerStats.delivered} delivered
                </div>
              </div>
              <div className="stat-card">
                <div className="l">Haul value</div>
                <div className="v accent">{formatPrice(haulerStats.value)}</div>
                <div className="sub">across your hauls</div>
              </div>
            </>
          )}
        </div>
      )}

      <div className={`dashboard-cols ${bothRoles ? "two" : ""}`}>
        {me.profile.shipper_enabled && (
          <section>
            <div className="section-h">
              <h3>My loads</h3>
              {myLoads.length > 0 && (
                <Link to="/loads/new" className="hh-link">
                  Post another
                </Link>
              )}
            </div>
            {myLoads.length === 0 ? (
              <div className="empty">
                No active loads. <Link to="/loads/new">Post one →</Link>
              </div>
            ) : (
              <div className="load-list">
                {myLoads.map((l) => (
                  <LoadRow key={l.id} load={l} />
                ))}
              </div>
            )}
          </section>
        )}

        {me.profile.hauler_enabled && (
          <section>
            <div className="section-h">
              <h3>My hauls</h3>
              <Link to="/loads" className="hh-link">
                Browse loads
              </Link>
            </div>
            {myHauls.length === 0 ? (
              <div className="empty">
                No active hauls yet. <Link to="/loads">Find one →</Link>
              </div>
            ) : (
              <div className="load-list">
                {myHauls.map((l) => (
                  <LoadRow key={l.id} load={l} />
                ))}
              </div>
            )}
          </section>
        )}
      </div>
    </div>
  );
}
