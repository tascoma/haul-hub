import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { api, ApiError } from "../lib/api";
import type { Load, Payment } from "../lib/types";
import { formatDate, formatPrice, formatStatus } from "../lib/format";

interface ActionConfig {
  label: string;
  path: string;
  variant?: "primary" | "danger" | "accent";
  withReason?: boolean;
}

function availableActions(load: Load, viewerId: string): ActionConfig[] {
  const actions: ActionConfig[] = [];
  const isShipper = load.shipper_id === viewerId;
  const isAssignedHauler = load.hauler_id === viewerId;
  const isPotentialHauler = !isShipper && load.hauler_id === null;
  const isTerminal = load.status === "delivered" || load.status === "cancelled";

  if (load.status === "posted" && isPotentialHauler) {
    actions.push({ label: "Claim this load", path: "/accept", variant: "accent" });
  }
  if (load.status === "accepted" && isAssignedHauler) {
    actions.push({ label: "Mark picked up", path: "/pickup", variant: "primary" });
  }
  if (load.status === "picked_up" && isAssignedHauler) {
    actions.push({ label: "Mark in transit", path: "/in-transit", variant: "primary" });
  }
  if (load.status === "in_transit" && isAssignedHauler) {
    actions.push({ label: "Mark delivered", path: "/deliver", variant: "accent" });
  }
  if (!isTerminal && (isShipper || isAssignedHauler)) {
    actions.push({ label: "Cancel", path: "/cancel", variant: "danger", withReason: true });
  }
  return actions;
}

function RowKV({
  k,
  v,
  muted,
  positive,
  big,
}: {
  k: string;
  v: string;
  muted?: boolean;
  positive?: boolean;
  big?: boolean;
}) {
  const cls = ["kv-row"];
  if (muted) cls.push("muted");
  if (positive) cls.push("positive");
  if (big) cls.push("big");
  return (
    <div className={cls.join(" ")}>
      <span className="k">{k}</span>
      <span className="v">{v}</span>
    </div>
  );
}

export function LoadDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { me } = useAuth();
  const navigate = useNavigate();

  const [load, setLoad] = useState<Load | null>(null);
  const [payment, setPayment] = useState<Payment | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const fetchAll = async (loadId: string) => {
    setLoading(true);
    try {
      const l = await api.get<Load>(`/loads/${loadId}`);
      setLoad(l);
      try {
        const p = await api.get<Payment>(`/loads/${loadId}/payment`);
        setPayment(p);
      } catch {
        setPayment(null);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to load");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!id) return;
    fetchAll(id);
  }, [id]);

  if (loading) return <div className="muted">Loading…</div>;
  if (error) return <div className="error">{error}</div>;
  if (!load || !me) return null;

  const doAction = async (action: ActionConfig) => {
    let body: unknown = undefined;
    if (action.withReason) {
      const reason = window.prompt("Reason for cancelling? (optional)") ?? "";
      body = { reason: reason || null };
    }
    setBusy(action.path);
    setError(null);
    try {
      await api.post<Load>(`/loads/${load.id}${action.path}`, body);
      await fetchAll(load.id);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Action failed");
    } finally {
      setBusy(null);
    }
  };

  const doDelete = async () => {
    if (!window.confirm("Take this load down? This can only be done before someone accepts.")) {
      return;
    }
    setBusy("delete");
    setError(null);
    try {
      await api.delete(`/loads/${load.id}`);
      navigate("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Delete failed");
    } finally {
      setBusy(null);
    }
  };

  const actions = availableActions(load, me.id);
  const isShipper = load.shipper_id === me.id;
  const canDelete = isShipper && (load.status === "posted" || load.status === "draft");
  const showPayout = payment !== null;

  const haulerPayout = payment
    ? formatPrice(payment.hauler_payout_cents)
    : formatPrice(Math.round(load.calculated_price_cents * 0.85));

  return (
    <div>
      <div className="page-h">
        <div>
          <div style={{ display: "flex", gap: 6, marginBottom: 10, flexWrap: "wrap" }}>
            <span
              className={`hh-pill ${load.urgency === "express" ? "hh-pill--accent" : ""}`}
            >
              {load.urgency === "express" ? "EXPRESS" : "STANDARD"}
            </span>
            <span className={`status-pill status-${load.status}`}>
              {formatStatus(load.status)}
            </span>
          </div>
          <h1 style={{ marginBottom: 6 }}>{load.title}</h1>
          {load.description && <div className="sub" style={{ marginTop: 4 }}>{load.description}</div>}
        </div>
      </div>

      <div className="dashboard-cols two">
        <div>
          {/* Route */}
          <div className="card">
            <div className="section-h">
              <h3>Route</h3>
              <span className="muted" style={{ fontSize: 12, fontWeight: 600 }}>
                {load.estimated_distance_miles} mi
              </span>
            </div>
            <div className="hh-route" style={{ marginTop: 6 }}>
              <span className="hh-route__dot" />
              <div>
                <div className="hh-route__where">
                  {load.pickup_address}, {load.pickup_city}, {load.pickup_state} {load.pickup_zip}
                </div>
                <div className="hh-route__sub">
                  Pickup window: {formatDate(load.pickup_window_start)} —{" "}
                  {formatDate(load.pickup_window_end)}
                </div>
              </div>
              <span className="hh-route__dot hh-route__dot--end" />
              <div>
                <div className="hh-route__where">
                  {load.dropoff_address}, {load.dropoff_city}, {load.dropoff_state}{" "}
                  {load.dropoff_zip}
                </div>
                <div className="hh-route__sub">
                  Deliver by: {formatDate(load.dropoff_by)}
                </div>
              </div>
            </div>
          </div>

          {/* Cargo */}
          <div className="card">
            <h3>Cargo</h3>
            <div className="hh-stat-row">
              <div>
                <div className="hh-stat__v">{load.weight_lbs.toLocaleString()}</div>
                <div className="hh-stat__l">lb</div>
              </div>
              <div>
                <div className="hh-stat__v">
                  {load.length_ft ?? "—"} × {load.width_ft ?? "—"}
                </div>
                <div className="hh-stat__l">ft (L × W)</div>
              </div>
              <div>
                <div className="hh-stat__v">{load.height_ft ?? "—"}</div>
                <div className="hh-stat__l">ft tall</div>
              </div>
            </div>
          </div>
        </div>

        <div>
          {/* Payout */}
          <div className="card card-dark">
            <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between" }}>
              <div>
                <div
                  style={{
                    font: "600 11px var(--hh-font)",
                    color: "rgba(255,255,255,0.55)",
                    textTransform: "uppercase",
                    letterSpacing: 0.07,
                  }}
                >
                  {isShipper ? "Load price" : "Your payout"}
                </div>
                <div className="hh-display hh-display--lg" style={{ color: "#fff", marginTop: 6 }}>
                  {isShipper ? formatPrice(load.calculated_price_cents) : haulerPayout}
                </div>
              </div>
              <div style={{ textAlign: "right" }}>
                <div style={{ font: "500 12px var(--hh-font)", color: "rgba(255,255,255,0.55)" }}>
                  {load.urgency === "express" ? "Express urgency" : "Standard"}
                </div>
                <div
                  style={{
                    font: "500 12px var(--hh-font)",
                    color: "rgba(255,255,255,0.55)",
                    marginTop: 2,
                  }}
                >
                  Paid 24h after delivery
                </div>
              </div>
            </div>
          </div>

          {/* Payout breakdown (when payment exists) */}
          {showPayout && payment && (
            <div className="card">
              <h3>Payout breakdown</h3>
              <RowKV k="Load price" v={formatPrice(payment.amount_cents)} />
              <RowKV
                k="Platform fee"
                v={`−${formatPrice(payment.platform_fee_cents)}`}
                muted
              />
              <div className="hh-div" />
              <RowKV
                k={isShipper ? "Hauler payout" : "Your payout"}
                v={formatPrice(payment.hauler_payout_cents)}
                big
              />
              <div style={{ marginTop: 10 }}>
                <span className={`status-pill status-${payment.status}`}>
                  Payment: {formatStatus(payment.status)}
                </span>
              </div>
            </div>
          )}

          {/* Actions */}
          {(actions.length > 0 || canDelete) && (
            <div className="card">
              <h3>Actions</h3>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {actions.map((a) => (
                  <button
                    key={a.path}
                    type="button"
                    className={`${a.variant ?? "primary"} hh-btn--block`}
                    style={{ height: 48 }}
                    disabled={busy !== null}
                    onClick={() => doAction(a)}
                  >
                    {busy === a.path ? "Working…" : a.label}
                  </button>
                ))}
                {canDelete && (
                  <button
                    type="button"
                    className="outline hh-btn--block"
                    disabled={busy !== null}
                    onClick={doDelete}
                  >
                    {busy === "delete" ? "Removing…" : "Remove this load"}
                  </button>
                )}
              </div>
              {actions.some((a) => a.variant === "accent") && (
                <div
                  className="muted"
                  style={{ textAlign: "center", fontSize: 11, marginTop: 10 }}
                >
                  You can cancel up to 30 min before pickup, free.
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
