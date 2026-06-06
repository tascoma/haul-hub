import { useEffect, useState } from "react";
import { useAuth } from "../lib/auth";
import { api, ApiError } from "../lib/api";
import type { BusinessType, HaulerProfile } from "../lib/types";
import { VehicleManager } from "../components/VehicleManager";

// ─── helpers ────────────────────────────────────────────────────────────────

function initialsOf(value: string | null | undefined): string {
  if (!value) return "?";
  const parts = value.trim().split(/\s+/).slice(0, 2);
  return parts.map((p) => p[0]?.toUpperCase() ?? "").join("") || value[0]?.toUpperCase() || "?";
}

type SaveStatus = "idle" | "saving" | "saved" | "error";

function useSaveStatus() {
  const [status, setStatus] = useState<SaveStatus>("idle");
  const [msg, setMsg] = useState<string | null>(null);

  const start = () => { setStatus("saving"); setMsg(null); };
  const ok    = (m = "Saved.") => { setStatus("saved"); setMsg(m); setTimeout(() => setStatus("idle"), 3000); };
  const fail  = (e: unknown) => {
    setStatus("error");
    setMsg(e instanceof ApiError ? e.detail : "Save failed — please try again.");
  };
  return { status, msg, start, ok, fail };
}

// ─── sub-forms ───────────────────────────────────────────────────────────────

const LANGUAGES = [
  { value: "en", label: "English" },
  { value: "es", label: "Spanish" },
  { value: "fr", label: "French" },
  { value: "pt", label: "Portuguese" },
  { value: "zh", label: "Chinese" },
];

const TIMEZONES = [
  "America/New_York",
  "America/Chicago",
  "America/Denver",
  "America/Los_Angeles",
  "America/Phoenix",
  "America/Anchorage",
  "Pacific/Honolulu",
];

const BUSINESS_TYPES: { value: BusinessType; label: string }[] = [
  { value: "individual",   label: "Individual / sole proprietor" },
  { value: "llc",          label: "LLC" },
  { value: "corporation",  label: "Corporation" },
  { value: "partnership",  label: "Partnership" },
];

// ─── main component ──────────────────────────────────────────────────────────

export function ProfilePage() {
  const { me, refresh } = useAuth();

  // ── personal info state ──────────────────────────────────────────────────
  const [fullName,    setFullName]    = useState("");
  const [displayName, setDisplayName] = useState("");
  const [phone,       setPhone]       = useState("");
  const [bio,         setBio]         = useState("");
  const personalSave = useSaveStatus();

  // ── preferences state ────────────────────────────────────────────────────
  const [language,   setLanguage]   = useState("en");
  const [timezone,   setTimezone]   = useState("America/Los_Angeles");
  const [marketingOptIn, setMarketingOptIn] = useState(false);
  const prefSave = useSaveStatus();

  // ── password state ───────────────────────────────────────────────────────
  const [currentPw,  setCurrentPw]  = useState("");
  const [newPw,      setNewPw]      = useState("");
  const [confirmPw,  setConfirmPw]  = useState("");
  const pwSave = useSaveStatus();

  // ── home address state ───────────────────────────────────────────────────
  const [addressLine1,  setAddressLine1]  = useState("");
  const [addressCity,   setAddressCity]   = useState("");
  const [addressState,  setAddressState]  = useState("");
  const [addressZip,    setAddressZip]    = useState("");
  const addressSave = useSaveStatus();

  // ── hauler state ─────────────────────────────────────────────────────────
  const [haulerProfile,      setHaulerProfile]      = useState<HaulerProfile | null>(null);
  const [companyName,        setCompanyName]        = useState("");
  const [businessType,       setBusinessType]       = useState<BusinessType | "">("");
  const [yearsExp,           setYearsExp]           = useState("");
  const [haulerBio,          setHaulerBio]          = useState("");
  const [serviceRadius,      setServiceRadius]      = useState("25");
  const [acceptsDisposal,    setAcceptsDisposal]    = useState(true);
  const [acceptsDonation,    setAcceptsDonation]    = useState(true);
  const [acceptsHazardous,   setAcceptsHazardous]   = useState(false);
  const [currentlyAvailable, setCurrentlyAvailable] = useState(false);
  const haulerSave = useSaveStatus();

  // ── seed form from API ───────────────────────────────────────────────────
  useEffect(() => {
    if (!me) return;
    const p = me.profile;
    setFullName(p.full_name ?? "");
    setDisplayName(p.display_name ?? "");
    setPhone(p.phone ?? "");
    setBio(p.bio ?? "");
    setLanguage(p.preferred_language ?? "en");
    setTimezone(p.timezone ?? "America/Los_Angeles");
    setMarketingOptIn(p.marketing_opt_in ?? false);
    setAddressLine1(p.address_line1 ?? "");
    setAddressCity(p.address_city ?? "");
    setAddressState(p.address_state ?? "");
    setAddressZip(p.address_zip ?? "");

    if (p.hauler_enabled) {
      api.get<HaulerProfile>("/me/hauler-profile")
        .then((hp) => {
          setHaulerProfile(hp);
          setCompanyName(hp.company_name ?? "");
          setBusinessType(hp.business_type ?? "");
          setYearsExp(hp.years_experience?.toString() ?? "");
          setHaulerBio(hp.bio ?? "");
          setServiceRadius(hp.service_radius_miles?.toString() ?? "25");
          setAcceptsDisposal(hp.accepts_disposal_jobs);
          setAcceptsDonation(hp.accepts_donation_runs);
          setAcceptsHazardous(hp.accepts_hazardous);
          setCurrentlyAvailable(hp.currently_available);
        })
        .catch(() => {/* not yet created */});
    }
  }, [me]);

  if (!me) return null;

  const initials = initialsOf(me.profile.full_name || me.email);
  const verified = !!haulerProfile?.verified_at;

  // ── save handlers ────────────────────────────────────────────────────────
  const savePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPw !== confirmPw) {
      pwSave.fail(new ApiError(400, "New passwords don't match"));
      return;
    }
    pwSave.start();
    try {
      await api.patch("/me/password", { current_password: currentPw, new_password: newPw });
      setCurrentPw(""); setNewPw(""); setConfirmPw("");
      pwSave.ok("Password changed.");
    } catch (err) { pwSave.fail(err); }
  };

  const savePersonal = async (e: React.FormEvent) => {
    e.preventDefault();
    personalSave.start();
    try {
      await api.patch("/me", { full_name: fullName, display_name: displayName || null, phone: phone || null, bio: bio || null });
      await refresh();
      personalSave.ok("Personal info saved.");
    } catch (err) { personalSave.fail(err); }
  };

  const savePreferences = async (e: React.FormEvent) => {
    e.preventDefault();
    prefSave.start();
    try {
      await api.patch("/me", { preferred_language: language, timezone, marketing_opt_in: marketingOptIn });
      await refresh();
      prefSave.ok("Preferences saved.");
    } catch (err) { prefSave.fail(err); }
  };

  const saveAddress = async (e: React.FormEvent) => {
    e.preventDefault();
    addressSave.start();
    try {
      await api.patch("/me", {
        address_line1: addressLine1 || null,
        address_city: addressCity || null,
        address_state: addressState || null,
        address_zip: addressZip || null,
      });
      await refresh();
      addressSave.ok("Address saved.");
    } catch (err) { addressSave.fail(err); }
  };

  const saveHauler = async (e: React.FormEvent) => {
    e.preventDefault();
    haulerSave.start();
    const body = {
      company_name:        companyName || null,
      business_type:       businessType || null,
      years_experience:    yearsExp ? Number(yearsExp) : null,
      bio:                 haulerBio || null,
      service_radius_miles: Number(serviceRadius) || 25,
      accepts_disposal_jobs: acceptsDisposal,
      accepts_donation_runs: acceptsDonation,
      accepts_hazardous:   acceptsHazardous,
      currently_available: currentlyAvailable,
    };
    try {
      const updated = await api.patch<HaulerProfile>("/me/hauler-profile", body);
      setHaulerProfile(updated);
      haulerSave.ok("Hauler settings saved.");
    } catch (err) { haulerSave.fail(err); }
  };

  return (
    <div>
      {/* ── Hero ─────────────────────────────────────────────────────── */}
      <div className="page-h">
        <div>
          <h1>Profile</h1>
          <div className="sub">Manage your account details and preferences.</div>
        </div>
      </div>

      <div className="card" style={{ display: "flex", alignItems: "center", gap: 18, marginBottom: 24 }}>
        <span className="hh-avatar hh-avatar--xl hh-avatar--dark">{initials}</span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ font: "700 20px var(--hh-font-display)", letterSpacing: "-0.015em" }}>
            {me.profile.full_name || <span className="muted">Add your name</span>}
            {me.profile.display_name && (
              <span className="muted" style={{ fontWeight: 400, fontSize: 15, marginLeft: 8 }}>
                "{me.profile.display_name}"
              </span>
            )}
          </div>
          <div className="muted" style={{ fontSize: 13, marginTop: 4 }}>
            {me.email}
            {me.profile.phone && <> · {me.profile.phone}</>}
          </div>
          <div style={{ display: "flex", gap: 6, marginTop: 10, flexWrap: "wrap" }}>
            {me.profile.shipper_enabled && (
              <span className="hh-pill hh-pill--info">Shipper</span>
            )}
            {me.profile.hauler_enabled && (
              <span className="hh-pill hh-pill--accent">Hauler</span>
            )}
            {verified && <span className="hh-pill hh-pill--success">Verified</span>}
          </div>
        </div>
      </div>

      {/* ── Personal info + Preferences row ──────────────────────────── */}
      <div className="dashboard-cols two" style={{ marginBottom: 24 }}>

        {/* Personal info */}
        <form className="card form-grid" onSubmit={savePersonal}>
          <h2 style={{ marginTop: 0 }}>Personal info</h2>

          <div>
            <label htmlFor="full-name">Full name</label>
            <input
              id="full-name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Your legal name"
            />
          </div>

          <div>
            <label htmlFor="display-name">Display name <span className="muted">(optional)</span></label>
            <input
              id="display-name"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="How you appear to others"
            />
          </div>

          <div>
            <label htmlFor="phone">Phone number</label>
            <input
              id="phone"
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+1 555 000 0000"
            />
          </div>

          <div>
            <label htmlFor="bio">Bio <span className="muted">(optional)</span></label>
            <textarea
              id="bio"
              rows={3}
              value={bio}
              onChange={(e) => setBio(e.target.value)}
              placeholder="A short intro about yourself"
              style={{ resize: "vertical" }}
            />
          </div>

          <div className="actions">
            <button type="submit" className="accent" disabled={personalSave.status === "saving"}>
              {personalSave.status === "saving" ? "Saving…" : "Save personal info"}
            </button>
          </div>
          {personalSave.msg && (
            <div
              className="muted"
              style={{ fontSize: 12, color: personalSave.status === "error" ? "var(--hh-danger)" : undefined }}
            >
              {personalSave.msg}
            </div>
          )}
        </form>

        {/* Preferences */}
        <form className="card form-grid" onSubmit={savePreferences}>
          <h2 style={{ marginTop: 0 }}>Preferences</h2>

          <div>
            <label htmlFor="language">Language</label>
            <select
              id="language"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
            >
              {LANGUAGES.map((l) => (
                <option key={l.value} value={l.value}>{l.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="timezone">Timezone</label>
            <select
              id="timezone"
              value={timezone}
              onChange={(e) => setTimezone(e.target.value)}
            >
              {TIMEZONES.map((tz) => (
                <option key={tz} value={tz}>{tz.replace("America/", "").replace("Pacific/", "Pacific/").replace(/_/g, " ")}</option>
              ))}
            </select>
          </div>

          <div style={{ display: "flex", alignItems: "flex-start", gap: 10, paddingTop: 4 }}>
            <input
              id="marketing"
              type="checkbox"
              checked={marketingOptIn}
              onChange={(e) => setMarketingOptIn(e.target.checked)}
              style={{ marginTop: 2 }}
            />
            <label htmlFor="marketing" style={{ cursor: "pointer", marginBottom: 0, flex: 1, minWidth: 0 }}>
              <span style={{ fontWeight: 500 }}>Marketing emails</span>
              <div className="muted" style={{ fontSize: 12, marginTop: 2 }}>
                Receive tips, load alerts, and platform news.
              </div>
            </label>
          </div>

          <div className="actions">
            <button type="submit" className="primary" disabled={prefSave.status === "saving"}>
              {prefSave.status === "saving" ? "Saving…" : "Save preferences"}
            </button>
          </div>
          {prefSave.msg && (
            <div
              className="muted"
              style={{ fontSize: 12, color: prefSave.status === "error" ? "var(--hh-danger)" : undefined }}
            >
              {prefSave.msg}
            </div>
          )}
        </form>
      </div>

      {/* ── Home address ─────────────────────────────────────────────── */}
      <form className="card form-grid" onSubmit={saveAddress} style={{ marginBottom: 24 }}>
        <h2 style={{ marginTop: 0 }}>Home address</h2>

        <div>
          <label htmlFor="address-line1">Street address</label>
          <input
            id="address-line1"
            value={addressLine1}
            onChange={(e) => setAddressLine1(e.target.value)}
            placeholder="123 Main St"
          />
        </div>

        <div className="dashboard-cols two">
          <div>
            <label htmlFor="address-city">City</label>
            <input
              id="address-city"
              value={addressCity}
              onChange={(e) => setAddressCity(e.target.value)}
              placeholder="Austin"
            />
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "80px 1fr", gap: "0.75rem" }}>
            <div>
              <label htmlFor="address-state">State</label>
              <input
                id="address-state"
                value={addressState}
                onChange={(e) => setAddressState(e.target.value.toUpperCase().slice(0, 2))}
                placeholder="TX"
                maxLength={2}
              />
            </div>
            <div>
              <label htmlFor="address-zip">ZIP</label>
              <input
                id="address-zip"
                value={addressZip}
                onChange={(e) => setAddressZip(e.target.value)}
                placeholder="78701"
                maxLength={10}
              />
            </div>
          </div>
        </div>

        <div className="actions">
          <button type="submit" className="primary" disabled={addressSave.status === "saving"}>
            {addressSave.status === "saving" ? "Saving…" : "Save address"}
          </button>
        </div>
        {addressSave.msg && (
          <div
            className="muted"
            style={{ fontSize: 12, color: addressSave.status === "error" ? "var(--hh-danger)" : undefined }}
          >
            {addressSave.msg}
          </div>
        )}
      </form>

      {/* ── Change password ──────────────────────────────────────────── */}
      <form className="card form-grid" onSubmit={savePassword} style={{ marginBottom: 24 }}>
        <h2 style={{ marginTop: 0 }}>Change password</h2>

        <div>
          <label htmlFor="pw-current">Current password</label>
          <input
            id="pw-current"
            type="password"
            value={currentPw}
            onChange={(e) => setCurrentPw(e.target.value)}
            autoComplete="current-password"
            required
          />
        </div>

        <div className="dashboard-cols two">
          <div>
            <label htmlFor="pw-new">New password <span className="muted">(min 8 chars)</span></label>
            <input
              id="pw-new"
              type="password"
              value={newPw}
              onChange={(e) => setNewPw(e.target.value)}
              autoComplete="new-password"
              minLength={8}
              required
            />
          </div>
          <div>
            <label htmlFor="pw-confirm">Confirm new password</label>
            <input
              id="pw-confirm"
              type="password"
              value={confirmPw}
              onChange={(e) => setConfirmPw(e.target.value)}
              autoComplete="new-password"
              required
            />
          </div>
        </div>

        <div className="actions">
          <button type="submit" className="primary" disabled={pwSave.status === "saving"}>
            {pwSave.status === "saving" ? "Saving…" : "Change password"}
          </button>
        </div>
        {pwSave.msg && (
          <div
            className="muted"
            style={{ fontSize: 12, color: pwSave.status === "error" ? "var(--hh-danger)" : undefined }}
          >
            {pwSave.msg}
          </div>
        )}
      </form>

      {/* ── Hauler settings (conditional) ────────────────────────────── */}
      {me.profile.hauler_enabled && (
        <>
        <form className="card form-grid" onSubmit={saveHauler}>
          <div className="section-h" style={{ marginBottom: 4 }}>
            <h2 style={{ marginTop: 0 }}>Hauler settings</h2>
            {haulerProfile && (
              <span className={`hh-pill ${verified ? "hh-pill--success" : "hh-pill--warning"}`}>
                {verified ? "Verified" : "Pending review"}
              </span>
            )}
          </div>

          <div className="dashboard-cols two">
            <div>
              <label htmlFor="company-name">Company name <span className="muted">(optional)</span></label>
              <input
                id="company-name"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                placeholder="Your business name"
              />
            </div>

            <div>
              <label htmlFor="business-type">Business type</label>
              <select
                id="business-type"
                value={businessType}
                onChange={(e) => setBusinessType(e.target.value as BusinessType | "")}
              >
                <option value="">— select —</option>
                {BUSINESS_TYPES.map((bt) => (
                  <option key={bt.value} value={bt.value}>{bt.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="years-exp">Years of experience</label>
              <input
                id="years-exp"
                type="number"
                min={0}
                max={60}
                value={yearsExp}
                onChange={(e) => setYearsExp(e.target.value)}
                placeholder="e.g. 5"
              />
            </div>

            <div>
              <label htmlFor="service-radius">Service radius (miles)</label>
              <input
                id="service-radius"
                type="number"
                min={1}
                max={500}
                value={serviceRadius}
                onChange={(e) => setServiceRadius(e.target.value)}
              />
            </div>
          </div>

          <div>
            <label htmlFor="hauler-bio">Hauler bio <span className="muted">(optional)</span></label>
            <textarea
              id="hauler-bio"
              rows={3}
              value={haulerBio}
              onChange={(e) => setHaulerBio(e.target.value)}
              placeholder="Tell shippers about your experience and equipment"
              style={{ resize: "vertical" }}
            />
          </div>

          <div>
            <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 10 }}>Job preferences</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {[
                { id: "disposal", checked: acceptsDisposal, onChange: setAcceptsDisposal, label: "Disposal jobs", desc: "Haul items to a dump, recycling center, or landfill." },
                { id: "donation", checked: acceptsDonation, onChange: setAcceptsDonation, label: "Donation runs", desc: "Transport items to Goodwill, Habitat ReStores, or similar." },
                { id: "hazardous", checked: acceptsHazardous, onChange: setAcceptsHazardous, label: "Hazardous materials", desc: "Loads flagged as containing potentially hazardous items." },
              ].map(({ id, checked, onChange, label, desc }) => (
                <div key={id} style={{ display: "flex", alignItems: "flex-start", gap: 10 }}>
                  <input
                    id={id}
                    type="checkbox"
                    checked={checked}
                    onChange={(e) => onChange(e.target.checked)}
                    style={{ marginTop: 2 }}
                  />
                  <label htmlFor={id} style={{ cursor: "pointer", marginBottom: 0, flex: 1, minWidth: 0 }}>
                    <span style={{ fontWeight: 500 }}>{label}</span>
                    <div className="muted" style={{ fontSize: 12, marginTop: 2 }}>{desc}</div>
                  </label>
                </div>
              ))}
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "flex-start", gap: 10, paddingTop: 4 }}>
            <input
              id="available"
              type="checkbox"
              checked={currentlyAvailable}
              onChange={(e) => setCurrentlyAvailable(e.target.checked)}
              style={{ marginTop: 2 }}
            />
            <label htmlFor="available" style={{ cursor: "pointer", marginBottom: 0, flex: 1, minWidth: 0 }}>
              <span style={{ fontWeight: 500 }}>Currently available</span>
              <div className="muted" style={{ fontSize: 12, marginTop: 2 }}>
                Shippers can see you as available for new loads right now.
              </div>
            </label>
          </div>

          <div className="actions">
            <button type="submit" className="accent" disabled={haulerSave.status === "saving"}>
              {haulerSave.status === "saving" ? "Saving…" : "Save hauler settings"}
            </button>
          </div>
          {haulerSave.msg && (
            <div
              className="muted"
              style={{ fontSize: 12, color: haulerSave.status === "error" ? "var(--hh-danger)" : undefined }}
            >
              {haulerSave.msg}
            </div>
          )}
        </form>

        {/* Vehicles */}
        <VehicleManager />

        {/* Stripe Connect */}
        <StripeConnectCard connectAccountId={me.profile.stripe_connect_account_id} />
        </>
      )}
    </div>
  );
}

function StripeConnectCard({ connectAccountId }: { connectAccountId: string | null }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleConnect() {
    setLoading(true);
    setError(null);
    try {
      const { url } = await api.post<{ url: string }>("/me/connect-onboarding");
      window.location.href = url;
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Could not start Stripe onboarding.");
      setLoading(false);
    }
  }

  return (
    <div className="card">
      <h2 style={{ marginTop: 0 }}>Stripe payouts</h2>
      {connectAccountId ? (
        <>
          <p className="muted" style={{ marginBottom: "0.75rem" }}>
            Your Stripe account is connected. You can return to Stripe to update
            your payout details.
          </p>
          <button
            className="btn btn-secondary"
            onClick={handleConnect}
            disabled={loading}
          >
            {loading ? "Loading…" : "Manage Stripe account"}
          </button>
        </>
      ) : (
        <>
          <p className="muted" style={{ marginBottom: "0.75rem" }}>
            Connect a Stripe account to receive payouts when you complete hauls.
          </p>
          <button
            className="accent"
            onClick={handleConnect}
            disabled={loading}
          >
            {loading ? "Loading…" : "Connect Stripe account"}
          </button>
        </>
      )}
      {error && (
        <p style={{ color: "var(--hh-danger)", marginTop: "0.5rem", fontSize: 13 }}>
          {error}
        </p>
      )}
    </div>
  );
}
