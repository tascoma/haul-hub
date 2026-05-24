import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../lib/api";
import type { Load } from "../lib/types";
import { formatPrice, formatStatus } from "../lib/format";

export function BrowseLoadsPage() {
  const [loads, setLoads] = useState<Load[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [city, setCity] = useState("");
  const [stateAbbr, setStateAbbr] = useState("");

  const fetchLoads = (cityFilter: string, stateFilter: string) => {
    setLoading(true);
    const params = new URLSearchParams();
    if (cityFilter) params.set("city", cityFilter);
    if (stateFilter) params.set("state", stateFilter);
    const qs = params.toString();
    api
      .get<Load[]>(`/loads${qs ? `?${qs}` : ""}`)
      .then(setLoads)
      .catch((err) => setError(err instanceof ApiError ? err.detail : "Failed to load"))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchLoads("", "");
  }, []);

  const onFilter = (e: React.FormEvent) => {
    e.preventDefault();
    fetchLoads(city, stateAbbr);
  };

  return (
    <div>
      <h1>Available loads</h1>
      <form className="card form-grid" onSubmit={onFilter}>
        <div className="form-row">
          <div>
            <label htmlFor="fcity">Pickup city</label>
            <input id="fcity" value={city} onChange={(e) => setCity(e.target.value)} />
          </div>
          <div>
            <label htmlFor="fstate">Pickup state</label>
            <input
              id="fstate"
              maxLength={2}
              value={stateAbbr}
              onChange={(e) => setStateAbbr(e.target.value.toUpperCase())}
            />
          </div>
        </div>
        <div className="actions">
          <button type="submit" className="primary">Apply filters</button>
          <button
            type="button"
            className="secondary"
            onClick={() => {
              setCity("");
              setStateAbbr("");
              fetchLoads("", "");
            }}
          >
            Clear
          </button>
        </div>
      </form>

      {error && <div className="error">{error}</div>}
      {loading ? (
        <div className="muted">Loading…</div>
      ) : loads.length === 0 ? (
        <div className="muted">No posted loads match.</div>
      ) : (
        <div className="load-list">
          {loads.map((l) => (
            <Link key={l.id} to={`/loads/${l.id}`} className="load-card" style={{ color: "inherit" }}>
              <div>
                <div style={{ fontWeight: 600 }}>{l.title}</div>
                <div className="meta">
                  {l.pickup_city}, {l.pickup_state} → {l.dropoff_city}, {l.dropoff_state}
                </div>
                <div className="meta">
                  {l.weight_lbs.toLocaleString()} lbs · {l.estimated_distance_miles} mi · {l.urgency}
                </div>
              </div>
              <div style={{ textAlign: "right" }}>
                <div className="price">{formatPrice(l.calculated_price_cents)}</div>
                <span className={`status-pill status-${l.status}`}>{formatStatus(l.status)}</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
