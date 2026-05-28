import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, ApiError } from "../lib/api";
import type { Load } from "../lib/types";
import { formatPrice } from "../lib/format";
import { PickupsMap } from "../components/PickupsMap";

function formatPickupShort(iso: string): { date: string; time: string } {
  const d = new Date(iso);
  return {
    date: d.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" }),
    time: d.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" }),
  };
}

export function BrowseLoadsPage() {
  const navigate = useNavigate();
  const [loads, setLoads] = useState<Load[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [urgencyFilter, setUrgencyFilter] = useState<"all" | "express" | "standard">("all");
  const [nearMe, setNearMe] = useState(true);

  useEffect(() => {
    setLoading(true);
    setError(null);
    api
      .get<Load[]>(`/loads${nearMe ? "?near_me=true" : ""}`)
      .then(setLoads)
      .catch((err) => setError(err instanceof ApiError ? err.detail : "Failed to load"))
      .finally(() => setLoading(false));
  }, [nearMe]);

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
        <span style={{ flex: 1 }} />
        <span
          className={`filter-chip ${nearMe ? "active" : ""}`}
          onClick={() => setNearMe((v) => !v)}
          title="Show only loads within your service radius"
        >
          📍 In my radius
        </span>
      </div>

      {error && <div className="error">{error}</div>}

      {loading ? (
        <div className="empty">Loading…</div>
      ) : visible.length === 0 ? (
        <div className="empty">
          {nearMe
            ? "No posted loads within your service radius. Turn off “In my radius” to see all loads."
            : "No posted loads match. Try widening your filters."}
        </div>
      ) : (
        <div className="browse-split">
          <div className="browse-list">
            {visible.map((l, i) => {
              const featured = i === 0 && l.urgency === "express";
              const pickup = formatPickupShort(l.pickup_window_start);
              return (
                <Link
                  key={l.id}
                  to={`/hauler/loads/${l.id}`}
                  className={`load-card ${featured ? "featured" : ""}`}
                >
                  <div className="load-card-top">
                    <div className="title">
                      {l.title}
                      {l.urgency === "express" && (
                        <span className="hh-pill hh-pill--accent" style={{ height: 18, fontSize: 9, padding: "0 6px" }}>
                          EXP
                        </span>
                      )}
                    </div>
                    <div className="load-card-payout">{formatPrice(l.calculated_price_cents)}</div>
                  </div>
                  <div className="load-card-route">
                    {l.pickup_city}, {l.pickup_state}
                    <span className="arrow">→</span>
                    {l.dropoff_city}, {l.dropoff_state}
                  </div>
                  <div className="load-card-meta">
                    <span>{l.estimated_distance_miles} mi</span>
                    <span className="dot">·</span>
                    <span>{l.weight_lbs.toLocaleString()} lb</span>
                    <span className="dot">·</span>
                    <span>{pickup.date}, {pickup.time}</span>
                  </div>
                </Link>
              );
            })}
          </div>
          <div className="browse-map">
            <PickupsMap
              loads={visible}
              onSelect={(id) => navigate(`/hauler/loads/${id}`)}
              height="100%"
            />
          </div>
        </div>
      )}
    </div>
  );
}
