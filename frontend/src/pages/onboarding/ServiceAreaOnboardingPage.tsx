import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError } from "../../lib/api";

interface AddressRead {
  id: string;
}

export function ServiceAreaOnboardingPage() {
  const navigate = useNavigate();
  const [line1, setLine1] = useState("");
  const [line2, setLine2] = useState("");
  const [city, setCity] = useState("");
  const [stateCode, setStateCode] = useState("");
  const [postalCode, setPostalCode] = useState("");
  const [radius, setRadius] = useState(25);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const address = await api.post<AddressRead>("/me/addresses/raw", {
        line1,
        line2: line2 || null,
        city,
        state: stateCode,
        postal_code: postalCode,
        country: "US",
      });
      await api.patch("/me/hauler-profile", {
        home_base_address_id: address.id,
        service_radius_miles: radius,
      });
      navigate("/onboarding");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not save service area");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-card" style={{ maxWidth: 560 }}>
      <h1>Where do you haul?</h1>
      <div className="sub">
        We'll match you to loads within your service radius of this address.
      </div>
      <form className="form-grid" onSubmit={onSubmit}>
        <div>
          <label htmlFor="line1">Street address</label>
          <input
            id="line1"
            required
            value={line1}
            onChange={(e) => setLine1(e.target.value)}
          />
        </div>
        <div>
          <label htmlFor="line2">Apt / unit (optional)</label>
          <input id="line2" value={line2} onChange={(e) => setLine2(e.target.value)} />
        </div>
        <div className="form-row">
          <div>
            <label htmlFor="city">City</label>
            <input
              id="city"
              required
              value={city}
              onChange={(e) => setCity(e.target.value)}
            />
          </div>
          <div>
            <label htmlFor="state">State</label>
            <input
              id="state"
              required
              maxLength={2}
              placeholder="OR"
              value={stateCode}
              onChange={(e) => setStateCode(e.target.value.toUpperCase())}
            />
          </div>
        </div>
        <div>
          <label htmlFor="zip">ZIP code</label>
          <input
            id="zip"
            required
            value={postalCode}
            onChange={(e) => setPostalCode(e.target.value)}
          />
        </div>
        <div>
          <label htmlFor="radius">Service radius: {radius} miles</label>
          <input
            id="radius"
            type="range"
            min={5}
            max={250}
            step={5}
            value={radius}
            onChange={(e) => setRadius(Number(e.target.value))}
          />
        </div>
        <button
          type="submit"
          className="accent hh-btn--block"
          style={{ height: 48 }}
          disabled={submitting}
        >
          {submitting ? "Saving…" : "Finish setup"}
        </button>
        {error && <div className="error">{error}</div>}
      </form>
    </div>
  );
}
