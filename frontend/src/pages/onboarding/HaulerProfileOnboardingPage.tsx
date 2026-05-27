import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError } from "../../lib/api";

type BusinessType = "individual" | "llc" | "corporation" | "partnership";

interface HaulerProfileBody {
  company_name?: string | null;
  business_type?: BusinessType | null;
  years_experience?: number | null;
  bio?: string | null;
  accepts_disposal_jobs: boolean;
  accepts_donation_runs: boolean;
  accepts_hazardous: boolean;
}

export function HaulerProfileOnboardingPage() {
  const navigate = useNavigate();
  const [companyName, setCompanyName] = useState("");
  const [businessType, setBusinessType] = useState<BusinessType>("individual");
  const [yearsExperience, setYearsExperience] = useState("");
  const [bio, setBio] = useState("");
  const [acceptsDisposal, setAcceptsDisposal] = useState(true);
  const [acceptsDonation, setAcceptsDonation] = useState(true);
  const [acceptsHazardous, setAcceptsHazardous] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    const body: HaulerProfileBody = {
      company_name: companyName || null,
      business_type: businessType,
      years_experience: yearsExperience ? Number(yearsExperience) : null,
      bio: bio || null,
      accepts_disposal_jobs: acceptsDisposal,
      accepts_donation_runs: acceptsDonation,
      accepts_hazardous: acceptsHazardous,
    };
    try {
      await api.patch("/me/hauler-profile", body);
      navigate("/onboarding");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not save hauler profile");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-card" style={{ maxWidth: 560 }}>
      <h1>Set up your hauler profile</h1>
      <div className="sub">Tell customers a bit about your hauling operation.</div>
      <form className="form-grid" onSubmit={onSubmit}>
        <div>
          <label htmlFor="company_name">Company name (optional)</label>
          <input
            id="company_name"
            value={companyName}
            onChange={(e) => setCompanyName(e.target.value)}
          />
        </div>
        <div>
          <label htmlFor="business_type">Business type</label>
          <select
            id="business_type"
            value={businessType}
            onChange={(e) => setBusinessType(e.target.value as BusinessType)}
          >
            <option value="individual">Individual</option>
            <option value="llc">LLC</option>
            <option value="corporation">Corporation</option>
            <option value="partnership">Partnership</option>
          </select>
        </div>
        <div>
          <label htmlFor="years">Years of hauling experience</label>
          <input
            id="years"
            type="number"
            min={0}
            value={yearsExperience}
            onChange={(e) => setYearsExperience(e.target.value)}
          />
        </div>
        <div>
          <label htmlFor="bio">Short bio (optional)</label>
          <textarea
            id="bio"
            rows={3}
            value={bio}
            onChange={(e) => setBio(e.target.value)}
          />
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
            What jobs will you take?
          </legend>
          <label style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <input
              type="checkbox"
              checked={acceptsDisposal}
              onChange={(e) => setAcceptsDisposal(e.target.checked)}
            />
            Disposal jobs (junk → landfill / transfer station)
          </label>
          <label style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <input
              type="checkbox"
              checked={acceptsDonation}
              onChange={(e) => setAcceptsDonation(e.target.checked)}
            />
            Donation runs
          </label>
          <label style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <input
              type="checkbox"
              checked={acceptsHazardous}
              onChange={(e) => setAcceptsHazardous(e.target.checked)}
            />
            Hazardous materials
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
