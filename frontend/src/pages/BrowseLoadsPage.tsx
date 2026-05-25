import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../lib/api";
import type { Load } from "../lib/types";
import { formatPrice } from "../lib/format";

function formatPickupShort(iso: string): { date: string; time: string } {
  const d = new Date(iso);
  return {
    date: d.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" }),
    time: d.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" }),
  };
}

export function BrowseLoadsPage() {
  const [loads, setLoads] = useState<Load[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [city, setCity] = useState("");
  const [stateAbbr, setStateAbbr] = useState("");
  const [search, setSearch] = useState("");
  const [urgencyFilter, setUrgencyFilter] = useState<"all" | "express" | "standard">("all");

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

  const visible = useMemo(() => {
    const q = search.trim().toLowerCase();
    return loads.filter((l) => {
      if (urgencyFilter !== "all" && l.urgency !== urgencyFilter) return false;
      if (!q) return true;
      return (
        l.title.toLowerCase().includes(q) ||
        l.pickup_city.toLowerCase().includes(q) ||
        l.dropoff_city.toLowerCase().includes(q)
      );
    });
  }, [loads, search, urgencyFilter]);

  const onFilter = (e: React.FormEvent) => {
    e.preventDefault();
    fetchLoads(city, stateAbbr);
  };

  const clear = () => {
    setCity("");
    setStateAbbr("");
    setSearch("");
    setUrgencyFilter("all");
    fetchLoads("", "");
  };

  return (
    <div>
      <div className="page-h">
        <div>
          <h1>Available loads</h1>
          <div className="sub">
            {loading ? "Loading…" : `${visible.length} ${visible.length === 1 ? "load" : "loads"} matching your filters`}
          </div>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <input
            placeholder="Search by city, title…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ height: 40, width: 260 }}
          />
        </div>
      </div>

      <div className="filter-bar">
        <span
          className={`filter-chip ${urgencyFilter === "all" ? "active" : ""}`}
          onClick={() => setUrgencyFilter("all")}
        >
          All
        </span>
        <span
          className={`filter-chip ${urgencyFilter === "express" ? "active" : ""}`}
          onClick={() => setUrgencyFilter("express")}
        >
          Express
        </span>
        <span
          className={`filter-chip ${urgencyFilter === "standard" ? "active" : ""}`}
          onClick={() => setUrgencyFilter("standard")}
        >
          Standard
        </span>
      </div>

      <form
        className="card form-grid"
        onSubmit={onFilter}
        style={{ marginBottom: 18 }}
      >
        <div className="section-h">
          <h3>Pickup location</h3>
        </div>
        <div className="form-row">
          <div>
            <label htmlFor="fcity">City</label>
            <input id="fcity" value={city} onChange={(e) => setCity(e.target.value)} />
          </div>
          <div>
            <label htmlFor="fstate">State</label>
            <input
              id="fstate"
              maxLength={2}
              value={stateAbbr}
              onChange={(e) => setStateAbbr(e.target.value.toUpperCase())}
            />
          </div>
        </div>
        <div className="actions">
          <button type="submit" className="primary">
            Apply filters
          </button>
          <button type="button" className="secondary" onClick={clear}>
            Clear
          </button>
        </div>
      </form>

      {error && <div className="error">{error}</div>}

      {!loading && visible.length === 0 ? (
        <div className="empty">No posted loads match. Try widening your filters.</div>
      ) : (
        <div className="loads-table">
          <div className="loads-table-head">
            <span>Load</span>
            <span>Route</span>
            <span className="col-cargo">Cargo</span>
            <span className="col-when">When</span>
            <span style={{ textAlign: "right" }}>Payout</span>
            <span className="col-action" />
          </div>
          {visible.map((l, i) => {
            const featured = i === 0 && l.urgency === "express";
            const pickup = formatPickupShort(l.pickup_window_start);
            return (
              <Link
                key={l.id}
                to={`/loads/${l.id}`}
                className={`loads-table-row ${featured ? "featured" : ""}`}
                style={{ color: "inherit", textDecoration: "none", display: "grid" }}
              >
                <div style={{ minWidth: 0 }}>
                  <div className="title">
                    {l.title}
                    {l.urgency === "express" && (
                      <span className="hh-pill hh-pill--accent" style={{ height: 18, fontSize: 9, padding: "0 6px" }}>
                        EXP
                      </span>
                    )}
                  </div>
                  <div className="sub">
                    <span className="hh-mono">#{l.id.slice(0, 6)}</span>
                  </div>
                </div>
                <div style={{ font: "600 12px var(--hh-font)", color: "var(--hh-ink-800)" }}>
                  {l.pickup_city}, {l.pickup_state}
                  <span style={{ color: "var(--hh-ink-400)", margin: "0 6px" }}>→</span>
                  {l.dropoff_city}, {l.dropoff_state}
                  <div className="sub">{l.estimated_distance_miles} mi</div>
                </div>
                <div className="col-cargo" style={{ font: "500 12px var(--hh-font)", color: "var(--hh-ink-700)" }}>
                  {l.weight_lbs.toLocaleString()} lb
                  <div className="sub">{l.urgency}</div>
                </div>
                <div className="col-when" style={{ font: "500 12px var(--hh-font)", color: "var(--hh-ink-700)" }}>
                  {pickup.date}
                  <div className="sub">{pickup.time}</div>
                </div>
                <div className="col-payout">{formatPrice(l.calculated_price_cents)}</div>
                <div className="col-action">
                  <span className={`btn-sm ${featured ? "accent" : "secondary"}`} style={{ display: "inline-flex" }}>
                    {featured ? "Claim" : "View"}
                  </span>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
