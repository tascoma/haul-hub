import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { api, ApiError } from "../lib/api";
import type { Load } from "../lib/types";
import { formatPrice, formatStatus } from "../lib/format";

function LoadRow({ load }: { load: Load }) {
  return (
    <Link to={`/loads/${load.id}`} className="load-card" style={{ color: "inherit" }}>
      <div>
        <div style={{ fontWeight: 600 }}>{load.title}</div>
        <div className="meta">
          {load.pickup_city}, {load.pickup_state} → {load.dropoff_city}, {load.dropoff_state}
        </div>
        <div className="meta">
          {load.weight_lbs.toLocaleString()} lbs · {load.estimated_distance_miles} mi ·{" "}
          {load.urgency}
        </div>
      </div>
      <div style={{ textAlign: "right" }}>
        <div className="price">{formatPrice(load.calculated_price_cents)}</div>
        <span className={`status-pill status-${load.status}`}>{formatStatus(load.status)}</span>
      </div>
    </Link>
  );
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

  return (
    <div>
      <h1>Welcome, {me.profile.full_name || me.email}</h1>

      {!me.profile.hauler_enabled && (
        <div className="card">
          Want to haul loads too?{" "}
          <Link to="/profile">Enable your hauler role from your profile.</Link>
        </div>
      )}

      {error && <div className="error">{error}</div>}
      {loading && <div className="muted">Loading loads…</div>}

      <div className={`dashboard-cols ${bothRoles ? "two" : ""}`}>
        {me.profile.shipper_enabled && (
          <section>
            <h2>My loads</h2>
            <p className="muted" style={{ marginTop: 0 }}>
              Loads you've posted (currently visible while still in 'posted' status).
            </p>
            {myLoads.length === 0 ? (
              <div className="muted">No active loads. <Link to="/loads/new">Post one.</Link></div>
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
            <h2>My hauls</h2>
            <p className="muted" style={{ marginTop: 0 }}>
              Loads you've accepted. <Link to="/loads">Browse new loads</Link> to find more.
            </p>
            {myHauls.length === 0 ? (
              <div className="muted">No active hauls yet.</div>
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
