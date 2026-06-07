import { useEffect, useState } from "react";
import {
  CardCvcElement,
  CardExpiryElement,
  CardNumberElement,
  useElements,
  useStripe,
} from "@stripe/react-stripe-js";
import { api, ApiError } from "../lib/api";
import { useAuth } from "../lib/auth";
import type { PaymentMethodInfo } from "../lib/types";

type Status = "idle" | "loading" | "saving" | "saved" | "error";

const ELEMENT_STYLE = {
  style: {
    base: { fontSize: "15px", color: "#1a1a1a" },
  },
};

const fieldStyle: React.CSSProperties = {
  border: "1px solid var(--border, #d1d5db)",
  borderRadius: 6,
  padding: "0.625rem 0.75rem",
  background: "#fff",
};

function cardBrandLabel(brand: string): string {
  const map: Record<string, string> = {
    visa: "Visa",
    mastercard: "Mastercard",
    amex: "American Express",
    discover: "Discover",
    jcb: "JCB",
    unionpay: "UnionPay",
    diners: "Diners Club",
  };
  return map[brand] ?? brand;
}

export function PaymentMethodPage() {
  const stripe = useStripe();
  const elements = useElements();
  const { me } = useAuth();

  const [saved, setSaved] = useState<PaymentMethodInfo | null>(null);
  const [replacing, setReplacing] = useState(false);
  const [status, setStatus] = useState<Status>("loading");
  const [error, setError] = useState<string | null>(null);

  // Billing address state
  const [billingSameAsHome, setBillingSameAsHome] = useState(true);
  const [billingLine1, setBillingLine1] = useState("");
  const [billingCity, setBillingCity] = useState("");
  const [billingState, setBillingState] = useState("");
  const [billingZip, setBillingZip] = useState("");
  const [billingSaveStatus, setBillingSaveStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [billingSaveMsg, setBillingSaveMsg] = useState<string | null>(null);

  // Seed billing state from profile
  useEffect(() => {
    if (!me) return;
    const p = me.profile;
    setBillingSameAsHome(p.billing_same_as_home);
    setBillingLine1(p.billing_address_line1 ?? "");
    setBillingCity(p.billing_address_city ?? "");
    setBillingState(p.billing_address_state ?? "");
    setBillingZip(p.billing_address_zip ?? "");
  }, [me]);

  useEffect(() => {
    api
      .get<PaymentMethodInfo>("/me/payment-method")
      .then((card) => {
        setSaved(card);
        setStatus("idle");
      })
      .catch((e) => {
        if (e instanceof ApiError && e.status === 404) {
          setStatus("idle");
        } else {
          setError("Could not load payment method.");
          setStatus("error");
        }
      });
  }, []);

  function effectiveBillingAddress() {
    if (billingSameAsHome && me) {
      return {
        line1: me.profile.address_line1 ?? "",
        city: me.profile.address_city ?? "",
        state: me.profile.address_state ?? "",
        postal_code: me.profile.address_zip ?? "",
      };
    }
    return { line1: billingLine1, city: billingCity, state: billingState, postal_code: billingZip };
  }

  async function saveBillingAddress(e: React.FormEvent) {
    e.preventDefault();
    setBillingSaveStatus("saving");
    setBillingSaveMsg(null);
    try {
      await api.patch("/me", {
        billing_same_as_home: billingSameAsHome,
        billing_address_line1: billingSameAsHome ? null : (billingLine1 || null),
        billing_address_city: billingSameAsHome ? null : (billingCity || null),
        billing_address_state: billingSameAsHome ? null : (billingState || null),
        billing_address_zip: billingSameAsHome ? null : (billingZip || null),
      });
      setBillingSaveStatus("saved");
      setBillingSaveMsg("Billing address saved.");
      setTimeout(() => setBillingSaveStatus("idle"), 3000);
    } catch (e) {
      setBillingSaveStatus("error");
      setBillingSaveMsg(e instanceof ApiError ? e.detail : "Could not save billing address.");
    }
  }

  async function handleSave() {
    if (!stripe || !elements) return;
    const cardNumber = elements.getElement(CardNumberElement);
    if (!cardNumber) return;

    setStatus("saving");
    setError(null);

    try {
      const { client_secret } = await api.post<{ client_secret: string }>(
        "/me/payment-method/setup-intent",
      );

      const addr = effectiveBillingAddress();
      const result = await stripe.confirmCardSetup(client_secret, {
        payment_method: {
          card: cardNumber,
          billing_details: {
            name: me?.profile.full_name ?? undefined,
            address: {
              line1: addr.line1 || undefined,
              city: addr.city || undefined,
              state: addr.state || undefined,
              postal_code: addr.postal_code || undefined,
              country: "US",
            },
          },
        },
      });

      if (result.error) {
        setError(result.error.message ?? "Card setup failed.");
        setStatus("error");
        return;
      }

      const pmId = result.setupIntent?.payment_method;
      if (!pmId || typeof pmId !== "string") {
        setError("Unexpected response from Stripe.");
        setStatus("error");
        return;
      }

      const info = await api.post<PaymentMethodInfo>("/me/payment-method", {
        payment_method_id: pmId,
      });
      setSaved(info);
      setReplacing(false);
      setStatus("saved");
      setTimeout(() => setStatus("idle"), 3000);
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Could not save card.");
      setStatus("error");
    }
  }

  if (status === "loading") {
    return (
      <div className="page-container">
        <p className="muted">Loading…</p>
      </div>
    );
  }

  const homeAddress = me?.profile;
  const hasHomeAddress = !!(homeAddress?.address_line1 && homeAddress?.address_city);

  return (
    <div className="page-container" style={{ maxWidth: 480 }}>
      <h1>Payment method</h1>
      <p className="muted" style={{ marginBottom: "1.5rem" }}>
        Your card is used to pay for loads you post. Funds are held when a
        hauler accepts and released to them on delivery.
      </p>

      {/* ── Saved card / card entry ── */}
      {saved && !replacing ? (
        <div className="card" style={{ marginBottom: "1rem" }}>
          <p>
            <strong>{cardBrandLabel(saved.brand)}</strong> ending in{" "}
            <strong>{saved.last4}</strong>
          </p>
          <p className="muted">
            Expires {saved.exp_month}/{saved.exp_year}
          </p>
          <button
            className="btn btn-secondary"
            style={{ marginTop: "0.75rem" }}
            onClick={() => setReplacing(true)}
          >
            Replace card
          </button>
        </div>
      ) : (
        <div className="card" style={{ marginBottom: "1rem", display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          <div>
            <label style={{ display: "block", marginBottom: "0.375rem", fontWeight: 600, fontSize: 14 }}>
              Card number
            </label>
            <div style={fieldStyle}>
              <CardNumberElement options={ELEMENT_STYLE} />
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
            <div>
              <label style={{ display: "block", marginBottom: "0.375rem", fontWeight: 600, fontSize: 14 }}>
                Expiry
              </label>
              <div style={fieldStyle}>
                <CardExpiryElement options={ELEMENT_STYLE} />
              </div>
            </div>
            <div>
              <label style={{ display: "block", marginBottom: "0.375rem", fontWeight: 600, fontSize: 14 }}>
                CVC
              </label>
              <div style={fieldStyle}>
                <CardCvcElement options={ELEMENT_STYLE} />
              </div>
            </div>
          </div>

          <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.25rem" }}>
            <button
              className="accent"
              onClick={handleSave}
              disabled={status === "saving" || !stripe}
            >
              {status === "saving" ? "Saving…" : "Save card"}
            </button>
            {replacing && (
              <button
                className="btn btn-secondary"
                onClick={() => { setReplacing(false); setError(null); }}
              >
                Cancel
              </button>
            )}
          </div>
        </div>
      )}

      {status === "saved" && (
        <p style={{ color: "var(--hh-success, green)" }}>Card saved successfully.</p>
      )}
      {error && <p style={{ color: "var(--hh-danger, red)" }}>{error}</p>}

      {/* ── Billing address ── */}
      <form className="card" onSubmit={saveBillingAddress} style={{ marginTop: "1.5rem", display: "flex", flexDirection: "column", gap: "0.75rem" }}>
        <h2 style={{ marginTop: 0, marginBottom: 0 }}>Billing address</h2>

        {/* Same as home toggle */}
        <div style={{ display: "flex", alignItems: "flex-start", gap: 10 }}>
          <input
            id="billing-same"
            type="checkbox"
            checked={billingSameAsHome}
            onChange={(e) => setBillingSameAsHome(e.target.checked)}
            style={{ marginTop: 3 }}
          />
          <label htmlFor="billing-same" style={{ cursor: "pointer", marginBottom: 0 }}>
            <span style={{ fontWeight: 500 }}>Same as home address</span>
            {billingSameAsHome && hasHomeAddress && (
              <div className="muted" style={{ fontSize: 12, marginTop: 2 }}>
                {homeAddress!.address_line1}, {homeAddress!.address_city}, {homeAddress!.address_state} {homeAddress!.address_zip}
              </div>
            )}
            {billingSameAsHome && !hasHomeAddress && (
              <div className="muted" style={{ fontSize: 12, marginTop: 2 }}>
                No home address saved — add one on your <a href="/profile" style={{ color: "var(--hh-accent)" }}>Profile</a> page.
              </div>
            )}
          </label>
        </div>

        {/* Custom billing address fields */}
        {!billingSameAsHome && (
          <>
            <div>
              <label htmlFor="billing-line1" style={{ display: "block", marginBottom: "0.375rem", fontWeight: 600, fontSize: 14 }}>
                Street address
              </label>
              <input
                id="billing-line1"
                value={billingLine1}
                onChange={(e) => setBillingLine1(e.target.value)}
                placeholder="123 Main St"
              />
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 80px 100px", gap: "0.75rem" }}>
              <div>
                <label htmlFor="billing-city" style={{ display: "block", marginBottom: "0.375rem", fontWeight: 600, fontSize: 14 }}>
                  City
                </label>
                <input
                  id="billing-city"
                  value={billingCity}
                  onChange={(e) => setBillingCity(e.target.value)}
                  placeholder="Austin"
                />
              </div>
              <div>
                <label htmlFor="billing-state" style={{ display: "block", marginBottom: "0.375rem", fontWeight: 600, fontSize: 14 }}>
                  State
                </label>
                <input
                  id="billing-state"
                  value={billingState}
                  onChange={(e) => setBillingState(e.target.value.toUpperCase().slice(0, 2))}
                  placeholder="TX"
                  maxLength={2}
                />
              </div>
              <div>
                <label htmlFor="billing-zip" style={{ display: "block", marginBottom: "0.375rem", fontWeight: 600, fontSize: 14 }}>
                  ZIP
                </label>
                <input
                  id="billing-zip"
                  value={billingZip}
                  onChange={(e) => setBillingZip(e.target.value)}
                  placeholder="78701"
                  maxLength={10}
                />
              </div>
            </div>
          </>
        )}

        <div>
          <button type="submit" className="primary" disabled={billingSaveStatus === "saving"}>
            {billingSaveStatus === "saving" ? "Saving…" : "Save billing address"}
          </button>
        </div>
        {billingSaveMsg && (
          <p
            className="muted"
            style={{ fontSize: 12, margin: 0, color: billingSaveStatus === "error" ? "var(--hh-danger)" : undefined }}
          >
            {billingSaveMsg}
          </p>
        )}
      </form>

      {!import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY && (
        <p className="muted" style={{ marginTop: "1rem", fontSize: "0.85rem" }}>
          Stripe is not configured. Set VITE_STRIPE_PUBLISHABLE_KEY in your
          .env.local to enable payments.
        </p>
      )}
    </div>
  );
}
