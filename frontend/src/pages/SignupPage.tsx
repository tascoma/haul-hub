import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { ApiError } from "../lib/api";

function Logomark() {
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 10 }}>
      <span
        style={{
          width: 36,
          height: 36,
          borderRadius: 10,
          background: "var(--hh-ink-900)",
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden>
          <path
            d="M2 7h11v9H2zM13 11h5l3 3v2h-8z"
            stroke="var(--hh-accent)"
            strokeWidth="2.2"
            strokeLinejoin="round"
          />
          <circle cx="7" cy="17.5" r="1.6" stroke="var(--hh-accent)" strokeWidth="2" />
          <circle cx="17" cy="17.5" r="1.6" stroke="var(--hh-accent)" strokeWidth="2" />
        </svg>
      </span>
      <span
        style={{
          font: "800 20px/1 var(--hh-font-display)",
          letterSpacing: "-0.025em",
          color: "var(--hh-ink-900)",
        }}
      >
        Haul Hub
      </span>
    </span>
  );
}

export function SignupPage() {
  const { signup } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await signup(email, password, fullName);
      navigate("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Sign-up failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-card">
      <Logomark />
      <h1>Create your account</h1>
      <div className="sub">
        Post a load or claim one — Haul Hub matches you with a hauler in minutes.
      </div>
      <form className="form-grid" onSubmit={onSubmit}>
        <div>
          <label htmlFor="name">Full name</label>
          <input id="name" value={fullName} onChange={(e) => setFullName(e.target.value)} />
        </div>
        <div>
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div>
          <label htmlFor="password">Password (min 8 chars)</label>
          <input
            id="password"
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        <button
          type="submit"
          className="accent hh-btn--block"
          style={{ height: 48 }}
          disabled={submitting}
        >
          {submitting ? "Creating…" : "Sign up"}
        </button>
        {error && <div className="error">{error}</div>}
      </form>
      <div className="auth-foot">
        Have an account? <Link to="/login">Log in</Link>
      </div>
    </div>
  );
}
