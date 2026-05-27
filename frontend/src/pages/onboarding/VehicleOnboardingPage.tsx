import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError } from "../../lib/api";

type VehicleType =
  | "pickup"
  | "pickup_with_trailer"
  | "flatbed"
  | "box_truck"
  | "cargo_van"
  | "semi"
  | "dump_truck"
  | "roll_off"
  | "other";

const VEHICLE_TYPES: Array<[VehicleType, string]> = [
  ["pickup", "Pickup truck"],
  ["pickup_with_trailer", "Pickup with trailer"],
  ["flatbed", "Flatbed"],
  ["box_truck", "Box truck"],
  ["cargo_van", "Cargo van"],
  ["semi", "Semi"],
  ["dump_truck", "Dump truck"],
  ["roll_off", "Roll-off"],
  ["other", "Other"],
];

export function VehicleOnboardingPage() {
  const navigate = useNavigate();
  const [nickname, setNickname] = useState("");
  const [vehicleType, setVehicleType] = useState<VehicleType>("pickup");
  const [make, setMake] = useState("");
  const [model, setModel] = useState("");
  const [year, setYear] = useState("");
  const [maxPayload, setMaxPayload] = useState("");
  const [hasLiftGate, setHasLiftGate] = useState(false);
  const [hasDolly, setHasDolly] = useState(false);
  const [hasStraps, setHasStraps] = useState(false);
  const [hasBlankets, setHasBlankets] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await api.post("/me/vehicles", {
        nickname: nickname || null,
        vehicle_type: vehicleType,
        make: make || null,
        model: model || null,
        year: year ? Number(year) : null,
        max_payload_lbs: maxPayload ? Number(maxPayload) : null,
        has_lift_gate: hasLiftGate,
        has_dolly: hasDolly,
        has_straps: hasStraps,
        has_blankets: hasBlankets,
        is_default: true,
      });
      navigate("/onboarding");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not save vehicle");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-card" style={{ maxWidth: 560 }}>
      <h1>Add your vehicle</h1>
      <div className="sub">
        We use this to match you with loads you can actually carry. You can add more later.
      </div>
      <form className="form-grid" onSubmit={onSubmit}>
        <div>
          <label htmlFor="nickname">Nickname (optional)</label>
          <input
            id="nickname"
            placeholder="e.g. Big Blue"
            value={nickname}
            onChange={(e) => setNickname(e.target.value)}
          />
        </div>
        <div>
          <label htmlFor="vehicle_type">Vehicle type</label>
          <select
            id="vehicle_type"
            value={vehicleType}
            onChange={(e) => setVehicleType(e.target.value as VehicleType)}
          >
            {VEHICLE_TYPES.map(([v, label]) => (
              <option key={v} value={v}>
                {label}
              </option>
            ))}
          </select>
        </div>
        <div className="form-row">
          <div>
            <label htmlFor="make">Make</label>
            <input id="make" value={make} onChange={(e) => setMake(e.target.value)} />
          </div>
          <div>
            <label htmlFor="model">Model</label>
            <input id="model" value={model} onChange={(e) => setModel(e.target.value)} />
          </div>
        </div>
        <div className="form-row">
          <div>
            <label htmlFor="year">Year</label>
            <input
              id="year"
              type="number"
              min={1950}
              max={new Date().getFullYear() + 1}
              value={year}
              onChange={(e) => setYear(e.target.value)}
            />
          </div>
          <div>
            <label htmlFor="payload">Max payload (lbs)</label>
            <input
              id="payload"
              type="number"
              min={0}
              value={maxPayload}
              onChange={(e) => setMaxPayload(e.target.value)}
            />
          </div>
        </div>
        <fieldset
          style={{
            border: "1px solid var(--hh-ink-100)",
            borderRadius: 12,
            padding: "12px 14px",
            display: "grid",
            gap: 8,
          }}
        >
          <legend style={{ padding: "0 6px", font: "700 12px var(--hh-font-display)" }}>
            Equipment
          </legend>
          <label style={{ display: "flex", gap: 8 }}>
            <input
              type="checkbox"
              checked={hasLiftGate}
              onChange={(e) => setHasLiftGate(e.target.checked)}
            />
            Lift gate
          </label>
          <label style={{ display: "flex", gap: 8 }}>
            <input
              type="checkbox"
              checked={hasDolly}
              onChange={(e) => setHasDolly(e.target.checked)}
            />
            Dolly
          </label>
          <label style={{ display: "flex", gap: 8 }}>
            <input
              type="checkbox"
              checked={hasStraps}
              onChange={(e) => setHasStraps(e.target.checked)}
            />
            Tie-down straps
          </label>
          <label style={{ display: "flex", gap: 8 }}>
            <input
              type="checkbox"
              checked={hasBlankets}
              onChange={(e) => setHasBlankets(e.target.checked)}
            />
            Moving blankets
          </label>
        </fieldset>
        <button
          type="submit"
          className="accent hh-btn--block"
          style={{ height: 48 }}
          disabled={submitting}
        >
          {submitting ? "Saving…" : "Continue"}
        </button>
        {error && <div className="error">{error}</div>}
      </form>
    </div>
  );
}
