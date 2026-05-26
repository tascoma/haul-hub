import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError } from "../lib/api";
import type { Load, LoadCreate, Urgency } from "../lib/types";

function toIsoLocal(value: string): string {
  // <input type="datetime-local"> gives YYYY-MM-DDTHH:mm with no tz; assume local.
  return new Date(value).toISOString();
}

function estimatePriceCents(weight: number, distance: number, urgency: Urgency): number {
  const base = 2000;
  const perMile = 180;
  const perLb = 4;
  const subtotal = base + Math.max(0, distance) * perMile + Math.max(0, weight) * perLb;
  return Math.round(urgency === "express" ? subtotal * 1.25 : subtotal);
}

export function PostLoadPage() {
  const navigate = useNavigate();

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");

  const [weightLbs, setWeightLbs] = useState("");
  const [lengthFt, setLengthFt] = useState("");
  const [widthFt, setWidthFt] = useState("");
  const [heightFt, setHeightFt] = useState("");

  const [pickupAddress, setPickupAddress] = useState("");
  const [pickupCity, setPickupCity] = useState("");
  const [pickupState, setPickupState] = useState("");
  const [pickupZip, setPickupZip] = useState("");
  const [pickupWindowStart, setPickupWindowStart] = useState("");
  const [pickupWindowEnd, setPickupWindowEnd] = useState("");

  const [dropoffAddress, setDropoffAddress] = useState("");
  const [dropoffCity, setDropoffCity] = useState("");
  const [dropoffState, setDropoffState] = useState("");
  const [dropoffZip, setDropoffZip] = useState("");
  const [dropoffBy, setDropoffBy] = useState("");

  const [distance, setDistance] = useState("");
  const [urgency, setUrgency] = useState<Urgency>("standard");

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const estimate = useMemo(() => {
    const w = Number(weightLbs) || 0;
    const d = Number(distance) || 0;
    if (!w && !d) return null;
    return estimatePriceCents(w, d, urgency);
  }, [weightLbs, distance, urgency]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    const body: LoadCreate = {
      title,
      description: description || null,
      weight_lbs: Number(weightLbs),
      length_ft: lengthFt ? Number(lengthFt) : null,
      width_ft: widthFt ? Number(widthFt) : null,
      height_ft: heightFt ? Number(heightFt) : null,
      pickup_address: pickupAddress,
      pickup_city: pickupCity,
      pickup_state: pickupState,
      pickup_zip: pickupZip,
      pickup_window_start: toIsoLocal(pickupWindowStart),
      pickup_window_end: toIsoLocal(pickupWindowEnd),
      dropoff_address: dropoffAddress,
      dropoff_city: dropoffCity,
      dropoff_state: dropoffState,
      dropoff_zip: dropoffZip,
      dropoff_by: toIsoLocal(dropoffBy),
      estimated_distance_miles: Number(distance),
      urgency,
    };
    try {
      const load = await api.post<Load>("/loads", body);
      navigate(`/loads/${load.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to post load");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      <div className="page-h">
        <div>
          <h1>Post a load</h1>
          <div className="sub">
            Tell us what you're moving — we'll match you with a hauler in minutes.
          </div>
        </div>
      </div>

      <div className="dashboard-cols two">
        <form className="form-grid" onSubmit={onSubmit}>
          <section className="card form-grid">
            <h2>What are we hauling?</h2>
            <div>
              <label htmlFor="title">Cargo title</label>
              <input
                id="title"
                placeholder="e.g. Upright piano — careful hands"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="desc">Description (optional)</label>
              <textarea
                id="desc"
                placeholder="Any details a hauler should know."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>
            <div className="form-row">
              <div>
                <label htmlFor="w">Weight (lbs)</label>
                <input
                  id="w"
                  type="number"
                  min={1}
                  required
                  value={weightLbs}
                  onChange={(e) => setWeightLbs(e.target.value)}
                />
              </div>
              <div>
                <label htmlFor="dist">Estimated distance (mi)</label>
                <input
                  id="dist"
                  type="number"
                  min={1}
                  required
                  value={distance}
                  onChange={(e) => setDistance(e.target.value)}
                />
              </div>
            </div>
            <div className="form-row">
              <div>
                <label htmlFor="len">Length (ft)</label>
                <input
                  id="len"
                  type="number"
                  min={0}
                  step={0.5}
                  value={lengthFt}
                  onChange={(e) => setLengthFt(e.target.value)}
                />
              </div>
              <div>
                <label htmlFor="wd">Width (ft)</label>
                <input
                  id="wd"
                  type="number"
                  min={0}
                  step={0.5}
                  value={widthFt}
                  onChange={(e) => setWidthFt(e.target.value)}
                />
              </div>
            </div>
            <div className="form-row">
              <div>
                <label htmlFor="ht">Height (ft)</label>
                <input
                  id="ht"
                  type="number"
                  min={0}
                  step={0.5}
                  value={heightFt}
                  onChange={(e) => setHeightFt(e.target.value)}
                />
              </div>
              <div>
                <label>Urgency</label>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                  {(["standard", "express"] as Urgency[]).map((opt) => {
                    const selected = urgency === opt;
                    return (
                      <button
                        key={opt}
                        type="button"
                        onClick={() => setUrgency(opt)}
                        style={{
                          height: 44,
                          padding: "0 12px",
                          borderRadius: 12,
                          border: selected
                            ? `1.5px solid var(--hh-${opt === "express" ? "accent" : "ink-900"})`
                            : "1px solid var(--hh-ink-200)",
                          background: selected
                            ? opt === "express"
                              ? "var(--hh-accent-soft)"
                              : "var(--hh-ink-50)"
                            : "var(--hh-paper)",
                          color: selected
                            ? opt === "express"
                              ? "var(--hh-accent-text)"
                              : "var(--hh-ink-900)"
                            : "var(--hh-ink-700)",
                          font: "700 13px var(--hh-font-display)",
                          textTransform: "capitalize",
                        }}
                      >
                        {opt}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          </section>

          <section className="card form-grid">
            <h2>Pickup</h2>
            <div>
              <label htmlFor="pa">Street address</label>
              <input
                id="pa"
                required
                value={pickupAddress}
                onChange={(e) => setPickupAddress(e.target.value)}
              />
            </div>
            <div className="form-row">
              <div>
                <label htmlFor="pc">City</label>
                <input
                  id="pc"
                  required
                  value={pickupCity}
                  onChange={(e) => setPickupCity(e.target.value)}
                />
              </div>
              <div>
                <label htmlFor="ps">State</label>
                <input
                  id="ps"
                  required
                  maxLength={2}
                  value={pickupState}
                  onChange={(e) => setPickupState(e.target.value.toUpperCase())}
                />
              </div>
            </div>
            <div className="form-row">
              <div>
                <label htmlFor="pz">ZIP</label>
                <input
                  id="pz"
                  required
                  value={pickupZip}
                  onChange={(e) => setPickupZip(e.target.value)}
                />
              </div>
              <div />
            </div>
            <div className="form-row">
              <div>
                <label htmlFor="pws">Pickup window start</label>
                <input
                  id="pws"
                  type="datetime-local"
                  required
                  value={pickupWindowStart}
                  onChange={(e) => setPickupWindowStart(e.target.value)}
                />
              </div>
              <div>
                <label htmlFor="pwe">Pickup window end</label>
                <input
                  id="pwe"
                  type="datetime-local"
                  required
                  value={pickupWindowEnd}
                  onChange={(e) => setPickupWindowEnd(e.target.value)}
                />
              </div>
            </div>
          </section>

          <section className="card form-grid">
            <h2>Dropoff</h2>
            <div>
              <label htmlFor="da">Street address</label>
              <input
                id="da"
                required
                value={dropoffAddress}
                onChange={(e) => setDropoffAddress(e.target.value)}
              />
            </div>
            <div className="form-row">
              <div>
                <label htmlFor="dc">City</label>
                <input
                  id="dc"
                  required
                  value={dropoffCity}
                  onChange={(e) => setDropoffCity(e.target.value)}
                />
              </div>
              <div>
                <label htmlFor="ds">State</label>
                <input
                  id="ds"
                  required
                  maxLength={2}
                  value={dropoffState}
                  onChange={(e) => setDropoffState(e.target.value.toUpperCase())}
                />
              </div>
            </div>
            <div className="form-row">
              <div>
                <label htmlFor="dz">ZIP</label>
                <input
                  id="dz"
                  required
                  value={dropoffZip}
                  onChange={(e) => setDropoffZip(e.target.value)}
                />
              </div>
              <div>
                <label htmlFor="db">Deliver by</label>
                <input
                  id="db"
                  type="datetime-local"
                  required
                  value={dropoffBy}
                  onChange={(e) => setDropoffBy(e.target.value)}
                />
              </div>
            </div>
          </section>

          {error && <div className="error">{error}</div>}

          <div className="actions">
            <button
              type="submit"
              className="accent"
              style={{ height: 48, padding: "0 22px" }}
              disabled={submitting}
            >
              {submitting ? "Posting…" : "Post load"}
            </button>
          </div>
        </form>

        {/* Live price preview */}
        <aside style={{ position: "sticky", top: 28, alignSelf: "start" }}>
          <div className="card card-dark">
            <div
              style={{
                font: "600 11px var(--hh-font)",
                color: "rgba(255,255,255,0.55)",
                textTransform: "uppercase",
                letterSpacing: 0.07,
              }}
            >
              Estimated price
            </div>
            <div className="hh-display hh-display--xl" style={{ color: "#fff", marginTop: 8 }}>
              {estimate !== null
                ? new Intl.NumberFormat("en-US", {
                    style: "currency",
                    currency: "USD",
                    maximumFractionDigits: 0,
                  }).format(estimate / 100)
                : "$—"}
            </div>
            <div
              style={{
                font: "500 12px var(--hh-font)",
                color: "rgba(255,255,255,0.55)",
                marginTop: 6,
              }}
            >
              {estimate !== null
                ? `${urgency === "express" ? "Express (+25%)" : "Standard"} · final price set on post`
                : "Enter weight + distance to see a price"}
            </div>
          </div>

          <div className="card">
            <h3>Match likelihood</h3>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 4 }}>
              <span
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: 99,
                  background: "var(--hh-success)",
                }}
              />
              <span
                style={{
                  font: "700 14px var(--hh-font-display)",
                  color: "var(--hh-success)",
                }}
              >
                High
              </span>
              <span className="muted" style={{ fontSize: 12, marginLeft: 6 }}>
                Most loads in your area are claimed within 15 min.
              </span>
            </div>
          </div>

          <div className="card">
            <h3>What happens next</h3>
            <ol style={{ paddingLeft: 18, margin: 0, color: "var(--hh-ink-600)", fontSize: 13, lineHeight: 1.5 }}>
              <li>We post your load to nearby haulers.</li>
              <li>A hauler claims it — you get notified.</li>
              <li>Track pickup → in transit → delivered.</li>
              <li>Pay when it lands. Rate your hauler.</li>
            </ol>
          </div>
        </aside>
      </div>
    </div>
  );
}
