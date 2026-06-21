import { Link } from "react-router-dom";

export function StripeReturnPage() {
  return (
    <div className="page-container" style={{ maxWidth: 480 }}>
      <h1>Stripe account connected</h1>
      <p style={{ marginBottom: "1.5rem" }}>
        Your Stripe account is set up. You can now receive payouts when you
        complete hauls.
      </p>
      <Link to="/hauler/dashboard" className="btn btn-primary">
        Go to dashboard
      </Link>
    </div>
  );
}
