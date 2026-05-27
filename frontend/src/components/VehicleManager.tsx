import { useEffect, useState } from "react";
import { api, ApiError } from "../lib/api";
import type { Vehicle, VehicleType } from "../lib/types";

// ─── constants ───────────────────────────────────────────────────────────────

const VEHICLE_TYPES: { value: VehicleType; label: string }[] = [
  { value: "pickup",              label: "Pickup truck" },
  { value: "pickup_with_trailer", label: "Pickup + trailer" },
  { value: "cargo_van",           label: "Cargo van" },
  { value: "box_truck",           label: "Box truck" },
  { value: "flatbed",             label: "Flatbed" },
  { value: "semi",                label: "Semi / 18-wheeler" },
  { value: "dump_truck",          label: "Dump truck" },
  { value: "roll_off",            label: "Roll-off" },
  { value: "other",               label: "Other" },
];

const TYPE_LABEL: Record<VehicleType, string> = Object.fromEntries(
  VEHICLE_TYPES.map(({ value, label }) => [value, label]),
) as Record<VehicleType, string>;

// ─── vehicle form (shared between add and edit) ───────────────────────────────

interface VehicleFormProps {
  initial?: Partial<Vehicle>;
  onSave: (data: VehicleFormData) => Promise<void>;
  onCancel: () => void;
  saving: boolean;
  error: string | null;
}

export interface VehicleFormData {
  vehicle_type: VehicleType;
  nickname: string;
  make: string;
  model: string;
  year: string;
  color: string;
  license_plate: string;
  license_plate_state: string;
  max_payload_lbs: string;
  has_lift_gate: boolean;
  has_dolly: boolean;
  has_straps: boolean;
  has_blankets: boolean;
  is_default: boolean;
}

function blankForm(v?: Partial<Vehicle>): VehicleFormData {
  return {
    vehicle_type:       (v?.vehicle_type ?? "pickup") as VehicleType,
    nickname:           v?.nickname           ?? "",
    make:               v?.make               ?? "",
    model:              v?.model              ?? "",
    year:               v?.year?.toString()   ?? "",
    color:              v?.color              ?? "",
    license_plate:      v?.license_plate      ?? "",
    license_plate_state: v?.license_plate_state ?? "",
    max_payload_lbs:    v?.max_payload_lbs?.toString() ?? "",
    has_lift_gate:      v?.has_lift_gate  ?? false,
    has_dolly:          v?.has_dolly      ?? false,
    has_straps:         v?.has_straps     ?? false,
    has_blankets:       v?.has_blankets   ?? false,
    is_default:         v?.is_default     ?? false,
  };
}

function VehicleForm({ initial, onSave, onCancel, saving, error }: VehicleFormProps) {
  const [form, setForm] = useState<VehicleFormData>(() => blankForm(initial));

  const set = <K extends keyof VehicleFormData>(k: K, v: VehicleFormData[K]) =>
    setForm((f) => ({ ...f, [k]: v }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSave(form);
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      <div className="dashboard-cols two">
        <div>
          <label htmlFor="vf-type">Vehicle type <span style={{ color: "var(--hh-danger)" }}>*</span></label>
          <select id="vf-type" value={form.vehicle_type} onChange={(e) => set("vehicle_type", e.target.value as VehicleType)} required>
            {VEHICLE_TYPES.map(({ value, label }) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="vf-nick">Nickname <span className="muted">(optional)</span></label>
          <input id="vf-nick" value={form.nickname} onChange={(e) => set("nickname", e.target.value)} placeholder="e.g. Big Blue" />
        </div>
        <div>
          <label htmlFor="vf-make">Make</label>
          <input id="vf-make" value={form.make} onChange={(e) => set("make", e.target.value)} placeholder="e.g. Ford" />
        </div>
        <div>
          <label htmlFor="vf-model">Model</label>
          <input id="vf-model" value={form.model} onChange={(e) => set("model", e.target.value)} placeholder="e.g. F-150" />
        </div>
        <div>
          <label htmlFor="vf-year">Year</label>
          <input id="vf-year" type="number" min={1980} max={new Date().getFullYear() + 1} value={form.year} onChange={(e) => set("year", e.target.value)} placeholder="e.g. 2020" />
        </div>
        <div>
          <label htmlFor="vf-color">Color</label>
          <input id="vf-color" value={form.color} onChange={(e) => set("color", e.target.value)} placeholder="e.g. White" />
        </div>
        <div>
          <label htmlFor="vf-plate">License plate</label>
          <input id="vf-plate" value={form.license_plate} onChange={(e) => set("license_plate", e.target.value)} placeholder="ABC-1234" />
        </div>
        <div>
          <label htmlFor="vf-state">Plate state</label>
          <input id="vf-state" value={form.license_plate_state} onChange={(e) => set("license_plate_state", e.target.value)} placeholder="e.g. CA" maxLength={2} />
        </div>
        <div>
          <label htmlFor="vf-payload">Max payload (lbs)</label>
          <input id="vf-payload" type="number" min={0} value={form.max_payload_lbs} onChange={(e) => set("max_payload_lbs", e.target.value)} placeholder="e.g. 2000" />
        </div>
      </div>

      {/* Equipment */}
      <div>
        <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 8, color: "var(--hh-ink-600)" }}>Equipment</div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
          {([
            { id: "vf-liftgate", key: "has_lift_gate",  label: "Lift gate" },
            { id: "vf-dolly",    key: "has_dolly",       label: "Dolly" },
            { id: "vf-straps",   key: "has_straps",      label: "Straps" },
            { id: "vf-blankets", key: "has_blankets",    label: "Moving blankets" },
          ] as { id: string; key: keyof VehicleFormData; label: string }[]).map(({ id, key, label }) => (
            <div key={id} style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <input
                id={id}
                type="checkbox"
                checked={form[key] as boolean}
                onChange={(e) => set(key, e.target.checked)}
                style={{ marginTop: 0 }}
              />
              <label htmlFor={id} style={{ cursor: "pointer", marginBottom: 0, fontSize: 13 }}>{label}</label>
            </div>
          ))}
        </div>
      </div>

      {/* Default */}
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <input
          id="vf-default"
          type="checkbox"
          checked={form.is_default}
          onChange={(e) => set("is_default", e.target.checked)}
          style={{ marginTop: 0 }}
        />
        <label htmlFor="vf-default" style={{ cursor: "pointer", marginBottom: 0, fontSize: 13 }}>
          Set as default vehicle
        </label>
      </div>

      {error && <div style={{ fontSize: 12, color: "var(--hh-danger)" }}>{error}</div>}

      <div style={{ display: "flex", gap: 8 }}>
        <button type="submit" className="accent hh-btn--sm" disabled={saving}>
          {saving ? "Saving…" : "Save vehicle"}
        </button>
        <button type="button" className="secondary hh-btn--sm" onClick={onCancel} disabled={saving}>
          Cancel
        </button>
      </div>
    </form>
  );
}

// ─── vehicle card ─────────────────────────────────────────────────────────────

interface VehicleCardProps {
  vehicle: Vehicle;
  onUpdate: (updated: Vehicle) => void;
  onRetire: (id: string) => void;
}

function VehicleCard({ vehicle, onUpdate, onRetire }: VehicleCardProps) {
  const [editing, setEditing] = useState(false);
  const [saving, setSaving]   = useState(false);
  const [retiring, setRetiring] = useState(false);
  const [error, setError]     = useState<string | null>(null);

  const title =
    vehicle.nickname
    || [vehicle.make, vehicle.model].filter(Boolean).join(" ")
    || TYPE_LABEL[vehicle.vehicle_type];

  const meta = [
    vehicle.make, vehicle.model,
    vehicle.year?.toString(),
    vehicle.color,
  ].filter(Boolean).join(" · ");

  const payload = vehicle.max_payload_lbs
    ? `${vehicle.max_payload_lbs.toLocaleString()} lb max`
    : null;

  const equipment = [
    vehicle.has_lift_gate && "Lift gate",
    vehicle.has_dolly     && "Dolly",
    vehicle.has_straps    && "Straps",
    vehicle.has_blankets  && "Blankets",
  ].filter(Boolean).join(" · ");

  const handleSave = async (data: VehicleFormData) => {
    setSaving(true);
    setError(null);
    try {
      const updated = await api.patch<Vehicle>(`/me/vehicles/${vehicle.id}`, {
        vehicle_type:        data.vehicle_type,
        nickname:            data.nickname || null,
        make:                data.make || null,
        model:               data.model || null,
        year:                data.year ? Number(data.year) : null,
        color:               data.color || null,
        license_plate:       data.license_plate || null,
        license_plate_state: data.license_plate_state || null,
        max_payload_lbs:     data.max_payload_lbs ? Number(data.max_payload_lbs) : null,
        has_lift_gate:       data.has_lift_gate,
        has_dolly:           data.has_dolly,
        has_straps:          data.has_straps,
        has_blankets:        data.has_blankets,
        is_default:          data.is_default,
      });
      onUpdate(updated);
      setEditing(false);
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const handleRetire = async () => {
    if (!confirm(`Retire "${title}"? It will no longer appear for new loads.`)) return;
    setRetiring(true);
    try {
      await api.delete(`/me/vehicles/${vehicle.id}`);
      onRetire(vehicle.id);
    } catch (e) {
      alert(e instanceof ApiError ? e.detail : "Could not retire vehicle");
      setRetiring(false);
    }
  };

  return (
    <div style={{
      border: "1px solid var(--hh-ink-200)",
      borderRadius: "var(--hh-r-md)",
      padding: "14px 16px",
      display: "flex",
      flexDirection: "column",
      gap: 10,
      background: vehicle.is_default ? "var(--hh-accent-soft)" : "var(--hh-ink-50)",
    }}>
      {/* header row */}
      <div style={{ display: "flex", alignItems: "flex-start", gap: 8 }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontWeight: 700, fontSize: 14, display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
            {title}
            {vehicle.is_default && (
              <span className="hh-pill hh-pill--accent" style={{ fontSize: 10 }}>Default</span>
            )}
            <span className="hh-pill" style={{ fontSize: 10, background: "var(--hh-ink-100)", color: "var(--hh-ink-600)" }}>
              {TYPE_LABEL[vehicle.vehicle_type]}
            </span>
          </div>
          {meta && <div className="muted" style={{ fontSize: 12, marginTop: 2 }}>{meta}</div>}
          {(payload || equipment) && (
            <div className="muted" style={{ fontSize: 12 }}>
              {[payload, equipment].filter(Boolean).join(" · ")}
            </div>
          )}
        </div>
        {!editing && (
          <div style={{ display: "flex", gap: 6, flexShrink: 0 }}>
            <button
              type="button"
              className="outline hh-btn--sm"
              onClick={() => setEditing(true)}
            >
              Edit
            </button>
            <button
              type="button"
              className="danger hh-btn--sm"
              onClick={handleRetire}
              disabled={retiring}
            >
              {retiring ? "…" : "Retire"}
            </button>
          </div>
        )}
      </div>

      {/* inline edit form */}
      {editing && (
        <div style={{ borderTop: "1px solid var(--hh-ink-200)", paddingTop: 14, marginTop: 2 }}>
          <VehicleForm
            initial={vehicle}
            onSave={handleSave}
            onCancel={() => { setEditing(false); setError(null); }}
            saving={saving}
            error={error}
          />
        </div>
      )}
    </div>
  );
}

// ─── main manager ─────────────────────────────────────────────────────────────

export function VehicleManager() {
  const [vehicles, setVehicles]     = useState<Vehicle[]>([]);
  const [loading, setLoading]       = useState(true);
  const [adding, setAdding]         = useState(false);
  const [addSaving, setAddSaving]   = useState(false);
  const [addError, setAddError]     = useState<string | null>(null);

  useEffect(() => {
    api.get<Vehicle[]>("/me/vehicles")
      .then((vs) => setVehicles(vs.filter((v) => v.status !== "retired")))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleAdd = async (data: VehicleFormData) => {
    setAddSaving(true);
    setAddError(null);
    try {
      const created = await api.post<Vehicle>("/me/vehicles", {
        vehicle_type:        data.vehicle_type,
        nickname:            data.nickname || null,
        make:                data.make || null,
        model:               data.model || null,
        year:                data.year ? Number(data.year) : null,
        color:               data.color || null,
        license_plate:       data.license_plate || null,
        license_plate_state: data.license_plate_state || null,
        max_payload_lbs:     data.max_payload_lbs ? Number(data.max_payload_lbs) : null,
        has_lift_gate:       data.has_lift_gate,
        has_dolly:           data.has_dolly,
        has_straps:          data.has_straps,
        has_blankets:        data.has_blankets,
        is_default:          data.is_default,
      });
      // If this vehicle is_default, clear other defaults locally
      setVehicles((prev) => {
        const updated = data.is_default
          ? prev.map((v) => ({ ...v, is_default: false }))
          : [...prev];
        return [...updated, created];
      });
      setAdding(false);
    } catch (e) {
      setAddError(e instanceof ApiError ? e.detail : "Could not add vehicle");
    } finally {
      setAddSaving(false);
    }
  };

  const handleUpdate = (updated: Vehicle) => {
    setVehicles((prev) => {
      let next = prev.map((v) => v.id === updated.id ? updated : v);
      // Clear other defaults if updated vehicle became default
      if (updated.is_default) {
        next = next.map((v) => v.id === updated.id ? v : { ...v, is_default: false });
      }
      return next;
    });
  };

  const handleRetire = (id: string) => {
    setVehicles((prev) => prev.filter((v) => v.id !== id));
  };

  return (
    <div className="card" style={{ marginTop: 0 }}>
      {/* header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>Vehicles</h2>
        {!adding && (
          <button type="button" className="outline hh-btn--sm" onClick={() => setAdding(true)}>
            + Add vehicle
          </button>
        )}
      </div>

      {/* add form */}
      {adding && (
        <div style={{
          border: "1px solid var(--hh-ink-200)",
          borderRadius: "var(--hh-r-md)",
          padding: "14px 16px",
          marginBottom: 12,
          background: "var(--hh-info-soft)",
        }}>
          <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 12, color: "var(--hh-ink-700)" }}>
            New vehicle
          </div>
          <VehicleForm
            onSave={handleAdd}
            onCancel={() => { setAdding(false); setAddError(null); }}
            saving={addSaving}
            error={addError}
          />
        </div>
      )}

      {/* vehicle list */}
      {loading ? (
        <div className="muted" style={{ fontSize: 13 }}>Loading vehicles…</div>
      ) : vehicles.length === 0 && !adding ? (
        <div className="muted" style={{ fontSize: 13 }}>
          No vehicles yet. Add one to start accepting loads.
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {vehicles.map((v) => (
            <VehicleCard
              key={v.id}
              vehicle={v}
              onUpdate={handleUpdate}
              onRetire={handleRetire}
            />
          ))}
        </div>
      )}
    </div>
  );
}
