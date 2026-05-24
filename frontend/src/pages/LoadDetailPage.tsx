import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { api, ApiError } from "../lib/api";
import type { Load, Payment } from "../lib/types";
import { formatDate, formatPrice, formatStatus } from "../lib/format";

interface ActionConfig {
  label: string;
  path: string;
  variant?: "primary" | "danger";
  withReason?: boolean;
}

function availableActions(load: Load, viewerId: string): ActionConfig[] {
  const actions: ActionConfig[] = [];
  const isShipper = load.shipper_id === viewerId;
  const isAssignedHauler = load.hauler_id === viewerId;
  const isPotentialHauler = !isShipper && load.hauler_id === null;
  const isTerminal = load.status === "delivered" || load.status === "cancelled";

  if (load.status === "posted" && isPotentialHauler) {
    actions.push({ label: "Accept this load", path: "/accept", variant: "primary" });
  }
  if (load.status === "accepted" && isAssignedHauler) {
    actions.push({ label: "Mark picked up", path: "/pickup", variant: "primary" });
  }
  if (load.status === "picked_up" && isAssignedHauler) {
    actions.push({ label: "Mark in transit", path: "/in-transit", variant: "primary" });
  }
  if (load.status === "in_transit" && isAssignedHauler) {
    actions.push({ label: "Mark delivered", path: "/deliver", variant: "primary" });
  }
  if (!isTerminal && (isShipper || isAssignedHauler)) {
    actions.push({ label: "Cancel", path: "/cancel", variant: "danger", withReason: true });
  }
  return actions;
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
        setPayment(null); // no payment yet (pre-acceptance)
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

  return (
    <div>
      <h1>{load.title}</h1>
      <div style={{ marginBottom: "1rem" }}>
        <span className={`status-pill status-${load.status}`}>{formatStatus(load.status)}</span>
      </div>

      {load.description && <p>{load.description}</p>}

      <div className="card">
        <h3>Route</h3>
        <p>
          <strong>From:</strong> {load.pickup_address}, {load.pickup_city}, {load.pickup_state}{" "}
          {load.pickup_zip}
        </p>
        <p>
          <strong>To:</strong> {load.dropoff_address}, {load.dropoff_city}, {load.dropoff_state}{" "}
          {load.dropoff_zip}
        </p>
        <p className="muted">
          {load.estimated_distance_miles} estimated miles · {load.urgency} urgency
        </p>
      </div>

      <div className="card">
        <h3>Schedule</h3>
        <p>
          <strong>Pickup window:</strong> {formatDate(load.pickup_window_start)} –{" "}
          {formatDate(load.pickup_window_end)}
        </p>
        <p>
          <strong>Deliver by:</strong> {formatDate(load.dropoff_by)}
        </p>
      </div>

      <div className="card">
        <h3>Cargo</h3>
        <p>
          <strong>Weight:</strong> {load.weight_lbs.toLocaleString()} lbs
        </p>
        {(load.length_ft || load.width_ft || load.height_ft) && (
          <p>
            <strong>Dimensions (L × W × H):</strong>{" "}
            {load.length_ft ?? "—"} × {load.width_ft ?? "—"} × {load.height_ft ?? "—"} ft
          </p>
        )}
      </div>

      <div className="card">
        <h3>Price</h3>
        <p style={{ fontSize: "1.5rem", fontWeight: 600 }}>
          {formatPrice(load.calculated_price_cents)}
        </p>
        {payment && (
          <>
            <p className="muted" style={{ fontSize: "0.9rem" }}>
              Platform fee: {formatPrice(payment.platform_fee_cents)} · Hauler payout:{" "}
              {formatPrice(payment.hauler_payout_cents)}
            </p>
            <p>
              <strong>Payment status:</strong>{" "}
              <span className={`status-pill status-${payment.status}`}>
                {formatStatus(payment.status)}
              </span>
            </p>
          </>
        )}
      </div>

      {(actions.length > 0 || canDelete) && (
        <div className="actions">
          {actions.map((a) => (
            <button
              key={a.path}
              type="button"
              className={a.variant === "danger" ? "danger" : "primary"}
              disabled={busy !== null}
              onClick={() => doAction(a)}
            >
              {busy === a.path ? "Working…" : a.label}
            </button>
          ))}
          {canDelete && (
            <button
              type="button"
              className="secondary"
              disabled={busy !== null}
              onClick={doDelete}
            >
              {busy === "delete" ? "Removing…" : "Remove load"}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
