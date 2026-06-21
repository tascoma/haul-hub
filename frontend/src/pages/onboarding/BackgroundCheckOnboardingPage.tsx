import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useStripe } from "@stripe/react-stripe-js";
import { api, ApiError } from "../../lib/api";

export function BackgroundCheckOnboardingPage() {
  const navigate = useNavigate();
  const stripe = useStripe();
  const [status, setStatus] = useState<"idle" | "loading" | "pending" | "error">("idle");
  const [error, setError] = useState<string | null>(null);

  const startVerification = async () => {
    setError(null);
    setStatus("loading");

    if (!stripe) {
      setError("Stripe has not loaded yet — please wait a moment and try again.");
      setStatus("error");
      return;
    }

    let clientSecret: string;
    try {
      const data = await api.post<{ client_secret: string }>("/me/stripe-identity-session");
      clientSecret = data.client_secret;
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not start verification");
      setStatus("error");
      return;
    }

    const result = await stripe.verifyIdentity(clientSecret);

    if (result.error) {
      if (result.error.code === "session_cancelled") {
        setStatus("idle");
      } else {
        setError(result.error.message ?? "Verification failed");
        setStatus("error");
      }
      return;
    }

    // Verification session submitted — backend will confirm via webhook.
    setStatus("pending");
    navigate("/onboarding");
  };

  return (
    <div className="auth-card" style={{ maxWidth: 520 }}>
      <h1>Background check</h1>
      <div className="sub" style={{ marginBottom: 24 }}>
        We use Stripe Identity to verify your identity as part of our background screening process.
        You'll be guided through a short document + selfie flow. This typically takes under 2
        minutes.
      </div>

      <div
        style={{
          background: "var(--hh-ink-50, #f8f8f8)",
          border: "1px solid var(--hh-ink-100)",
          borderRadius: 12,
          padding: "16px 20px",
          marginBottom: 24,
          fontSize: 14,
          lineHeight: 1.6,
        }}
      >
        <strong>What to have ready:</strong>
        <ul style={{ marginTop: 8, paddingLeft: 20 }}>
          <li>Government-issued photo ID (driver's license or passport)</li>
          <li>A device with a camera for the selfie step</li>
        </ul>
      </div>

      {status === "pending" && (
        <div
          style={{
            color: "var(--hh-success, #16a34a)",
            background: "#f0fdf4",
            border: "1px solid #bbf7d0",
            borderRadius: 10,
            padding: "12px 16px",
            marginBottom: 16,
            fontSize: 14,
          }}
        >
          ✓ Verification submitted — we'll review it shortly. You can continue setting up your
          account.
        </div>
      )}

      {error && <div className="error" style={{ marginBottom: 16 }}>{error}</div>}

      {status !== "pending" && (
        <button
          type="button"
          className="accent hh-btn--block"
          style={{ height: 48 }}
          disabled={status === "loading" || !stripe}
          onClick={startVerification}
        >
          {status === "loading" ? "Starting…" : "Start identity verification"}
        </button>
      )}

      {status === "pending" && (
        <button
          type="button"
          className="accent hh-btn--block"
          style={{ height: 48 }}
          onClick={() => navigate("/onboarding")}
        >
          Continue
        </button>
      )}

      {!import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY && (
        <p style={{ fontSize: 12, color: "var(--hh-ink-400)", marginTop: 12 }}>
          Stripe is not configured. Set VITE_STRIPE_PUBLISHABLE_KEY to enable identity verification.
        </p>
      )}
    </div>
  );
}
