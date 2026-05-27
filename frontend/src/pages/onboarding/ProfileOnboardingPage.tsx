import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError } from "../../lib/api";
import { useAuth } from "../../lib/auth";

export function ProfileOnboardingPage() {
  const { me, refresh } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState(me?.profile.full_name ?? "");
  const [phone, setPhone] = useState(me?.profile.phone ?? "");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await api.patch("/me", { full_name: fullName, phone });
      await refresh();
      navigate("/onboarding");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not save profile");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-card">
      <h1>Tell us about you</h1>
      <div className="sub">We need a name and phone number on file before you can use Haul Hub.</div>
      <form className="form-grid" onSubmit={onSubmit}>
        <div>
          <label htmlFor="full_name">Full name</label>
          <input
            id="full_name"
            required
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
          />
        </div>
        <div>
          <label htmlFor="phone">Phone</label>
          <input
            id="phone"
            type="tel"
            required
            placeholder="+15551234567"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
          />
        </div>
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
