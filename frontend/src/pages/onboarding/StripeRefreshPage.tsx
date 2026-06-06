import { useEffect, useState } from "react";
import { api, ApiError } from "../../lib/api";

export function StripeRefreshPage() {
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .post<{ url: string }>("/me/connect-onboarding")
      .then(({ url }) => {
        window.location.href = url;
      })
      .catch((e) => {
        setError(e instanceof ApiError ? e.detail : "Could not refresh onboarding link.");
      });
  }, []);

  if (error) {
    return (
      <div className="page-container" style={{ maxWidth: 480 }}>
        <h1>Something went wrong</h1>
        <p style={{ color: "var(--danger, red)" }}>{error}</p>
      </div>
    );
  }

  return (
    <div className="page-container" style={{ maxWidth: 480 }}>
      <p className="muted">Refreshing Stripe onboarding link…</p>
    </div>
  );
}
