import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError } from "../lib/api";
import type { Load, LoadCreate, Urgency } from "../lib/types";

function toIsoLocal(value: string): string {
  // <input type="datetime-local"> gives YYYY-MM-DDTHH:mm with no tz; assume local.
  return new Date(value).toISOString();
}

export function PostLoadPage() {
  const navigate = useNavigate();

  // Description
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");

  // Dimensions
  const [weightLbs, setWeightLbs] = useState("");
  const [lengthFt, setLengthFt] = useState("");
  const [widthFt, setWidthFt] = useState("");
  const [heightFt, setHeightFt] = useState("");

  // Pickup
  const [pickupAddress, setPickupAddress] = useState("");
  const [pickupCity, setPickupCity] = useState("");
  const [pickupState, setPickupState] = useState("");
  const [pickupZip, setPickupZip] = useState("");
  const [pickupWindowStart, setPickupWindowStart] = useState("");
  const [pickupWindowEnd, setPickupWindowEnd] = useState("");

  // Dropoff
  const [dropoffAddress, setDropoffAddress] = useState("");
  const [dropoffCity, setDropoffCity] = useState("");
  const [dropoffState, setDropoffState] = useState("");
  const [dropoffZip, setDropoffZip] = useState("");
  const [dropoffBy, setDropoffBy] = useState("");

  // Pricing inputs
  const [distance, setDistance] = useState("");
  const [urgency, setUrgency] = useState<Urgency>("standard");

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
      <h1>Post a load</h1>
      <form className="form-grid" onSubmit={onSubmit}>
        <section className="card form-grid">
          <h2>Description</h2>
          <div>
            <label htmlFor="title">Title</label>
            <input id="title" required value={title} onChange={(e) => setTitle(e.target.value)} />
          </div>
          <div>
            <label htmlFor="desc">Description</label>
            <textarea
              id="desc"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
        </section>

        <section className="card form-grid">
          <h2>Dimensions</h2>
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
              <label htmlFor="len">Length (ft)</label>
              <input id="len" type="number" min={0} step={0.5} value={lengthFt} onChange={(e) => setLengthFt(e.target.value)} />
            </div>
          </div>
          <div className="form-row">
            <div>
              <label htmlFor="wd">Width (ft)</label>
              <input id="wd" type="number" min={0} step={0.5} value={widthFt} onChange={(e) => setWidthFt(e.target.value)} />
            </div>
            <div>
              <label htmlFor="ht">Height (ft)</label>
              <input id="ht" type="number" min={0} step={0.5} value={heightFt} onChange={(e) => setHeightFt(e.target.value)} />
            </div>
          </div>
        </section>

        <section className="card form-grid">
          <h2>Pickup</h2>
          <div>
            <label htmlFor="pa">Street address</label>
            <input id="pa" required value={pickupAddress} onChange={(e) => setPickupAddress(e.target.value)} />
          </div>
          <div className="form-row">
            <div>
              <label htmlFor="pc">City</label>
              <input id="pc" required value={pickupCity} onChange={(e) => setPickupCity(e.target.value)} />
            </div>
            <div>
              <label htmlFor="ps">State</label>
              <input id="ps" required maxLength={2} value={pickupState} onChange={(e) => setPickupState(e.target.value.toUpperCase())} />
            </div>
          </div>
          <div className="form-row">
            <div>
              <label htmlFor="pz">ZIP</label>
              <input id="pz" required value={pickupZip} onChange={(e) => setPickupZip(e.target.value)} />
            </div>
          </div>
          <div className="form-row">
            <div>
              <label htmlFor="pws">Pickup window start</label>
              <input id="pws" type="datetime-local" required value={pickupWindowStart} onChange={(e) => setPickupWindowStart(e.target.value)} />
            </div>
            <div>
              <label htmlFor="pwe">Pickup window end</label>
              <input id="pwe" type="datetime-local" required value={pickupWindowEnd} onChange={(e) => setPickupWindowEnd(e.target.value)} />
            </div>
          </div>
        </section>

        <section className="card form-grid">
          <h2>Dropoff</h2>
          <div>
            <label htmlFor="da">Street address</label>
            <input id="da" required value={dropoffAddress} onChange={(e) => setDropoffAddress(e.target.value)} />
          </div>
          <div className="form-row">
            <div>
              <label htmlFor="dc">City</label>
              <input id="dc" required value={dropoffCity} onChange={(e) => setDropoffCity(e.target.value)} />
            </div>
            <div>
              <label htmlFor="ds">State</label>
              <input id="ds" required maxLength={2} value={dropoffState} onChange={(e) => setDropoffState(e.target.value.toUpperCase())} />
            </div>
          </div>
          <div className="form-row">
            <div>
              <label htmlFor="dz">ZIP</label>
              <input id="dz" required value={dropoffZip} onChange={(e) => setDropoffZip(e.target.value)} />
            </div>
            <div>
              <label htmlFor="db">Deliver by</label>
              <input id="db" type="datetime-local" required value={dropoffBy} onChange={(e) => setDropoffBy(e.target.value)} />
            </div>
          </div>
        </section>

        <section className="card form-grid">
          <h2>Pricing inputs</h2>
          <p className="muted" style={{ marginTop: 0 }}>
            Price is calculated from these inputs. (Distance is manual entry for the MVP — maps come later.)
          </p>
          <div className="form-row">
            <div>
              <label htmlFor="dist">Estimated distance (miles)</label>
              <input id="dist" type="number" min={1} required value={distance} onChange={(e) => setDistance(e.target.value)} />
            </div>
            <div>
              <label htmlFor="urg">Urgency</label>
              <select id="urg" value={urgency} onChange={(e) => setUrgency(e.target.value as Urgency)}>
                <option value="standard">Standard</option>
                <option value="express">Express (faster, higher price)</option>
              </select>
            </div>
          </div>
        </section>

        <div className="actions">
          <button type="submit" className="primary" disabled={submitting}>
            {submitting ? "Posting…" : "Post load"}
          </button>
        </div>
        {error && <div className="error">{error}</div>}
      </form>
    </div>
  );
}
