import { Link } from "react-router-dom";

function TruckIcon({ size = 24 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden>
      <path d="M2 7h11v9H2zM13 11h5l3 3v2h-8z" stroke="var(--hh-accent)" strokeWidth="2.2" strokeLinejoin="round" />
      <circle cx="7" cy="17.5" r="1.6" stroke="var(--hh-accent)" strokeWidth="2" />
      <circle cx="17" cy="17.5" r="1.6" stroke="var(--hh-accent)" strokeWidth="2" />
    </svg>
  );
}

const FEATURES = [
  {
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" aria-hidden>
        <path d="M12 5v14M5 12h14" stroke="var(--hh-accent)" strokeWidth="2" strokeLinecap="round" />
      </svg>
    ),
    title: "Post a Load in Minutes",
    body: "Describe your shipment, set your pickup and drop-off, and go live instantly. No phone calls, no back-and-forth.",
  },
  {
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" aria-hidden>
        <circle cx="12" cy="12" r="9" stroke="var(--hh-accent)" strokeWidth="2" />
        <path d="M12 7v5l3 3" stroke="var(--hh-accent)" strokeWidth="2" strokeLinecap="round" />
      </svg>
    ),
    title: "Real-Time Tracking",
    body: "Watch your load move from pickup to delivery on a live map. Know exactly where your freight is at every moment.",
  },
  {
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" aria-hidden>
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" stroke="var(--hh-accent)" strokeWidth="2" strokeLinecap="round" />
        <circle cx="9" cy="7" r="4" stroke="var(--hh-accent)" strokeWidth="2" />
        <path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" stroke="var(--hh-accent)" strokeWidth="2" strokeLinecap="round" />
      </svg>
    ),
    title: "Verified Haulers",
    body: "Every hauler on the platform is vetted, rated, and insured. You choose who moves your goods based on reviews and track record.",
  },
  {
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" aria-hidden>
        <rect x="2" y="5" width="20" height="14" rx="3" stroke="var(--hh-accent)" strokeWidth="2" />
        <path d="M2 10h20" stroke="var(--hh-accent)" strokeWidth="2" />
      </svg>
    ),
    title: "Secure Payments",
    body: "Payment is held in escrow until delivery is confirmed. Funds release automatically — no chasing invoices.",
  },
  {
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" aria-hidden>
        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="var(--hh-accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
    title: "Any Freight, Any Size",
    body: "Pallets, equipment, furniture, bulk cargo — if it needs moving, Haul Hub has the right truck for the job.",
  },
  {
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" aria-hidden>
        <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z" stroke="var(--hh-accent)" strokeWidth="2" />
      </svg>
    ),
    title: "24/7 Support",
    body: "Our team is always on. Whether a load is delayed or you need help with a booking, we pick up.",
  },
];

const STEPS = [
  { num: "01", title: "Create an account", body: "Sign up free in under 2 minutes. No subscription required." },
  { num: "02", title: "Post your load", body: "Add pickup & drop-off, dimensions, weight, and your preferred timeline." },
  { num: "03", title: "Accept a bid", body: "Haulers near you respond fast. Compare profiles, ratings, and prices." },
  { num: "04", title: "Delivered", body: "Track in real-time and release payment once your freight arrives safe." },
];

export function LandingPage() {
  return (
    <div className="landing">
      {/* ── Header ── */}
      <header className="landing-header">
        <div className="landing-header-inner">
          <Link to="/" className="landing-brand">
            <span className="landing-brand-mark">
              <TruckIcon size={20} />
            </span>
            <span className="landing-brand-name">Haul Hub</span>
          </Link>

          <nav className="landing-nav">
            <Link to="/login" className="hh-btn hh-btn--ghost landing-nav-login">
              Log in
            </Link>
            <Link to="/signup" className="hh-btn hh-btn--primary landing-nav-signup">
              Sign up free
            </Link>
          </nav>
        </div>
      </header>

      {/* ── Hero ── */}
      <section className="landing-hero">
        <div className="landing-container">
          <div className="landing-hero-eyebrow">
            <span className="hh-pill hh-pill--accent">Freight marketplace</span>
          </div>
          <h1 className="landing-hero-h1">
            Ship anything.<br />
            <span className="landing-hero-accent">Delivered fast.</span>
          </h1>
          <p className="landing-hero-sub">
            Haul Hub connects shippers with verified, independent haulers across the country.
            Post a load, get competitive bids, and track your freight in real time — all in one place.
          </p>
          <div className="landing-hero-cta">
            <Link to="/signup" className="hh-btn hh-btn--accent landing-cta-primary">
              Post a load — it's free
            </Link>
            <Link to="/login" className="hh-btn hh-btn--outline landing-cta-secondary">
              Log in to your account
            </Link>
          </div>
          <p className="landing-hero-note">No monthly fees &middot; Pay per shipment &middot; Cancel anytime</p>
        </div>
      </section>

      {/* ── Hauler CTA ── */}
      <section className="landing-container">
        <div className="landing-hauler-widget">
          <div className="landing-hauler-icon">
            <TruckIcon size={36} />
          </div>
          <div className="landing-hauler-copy">
            <h2 className="landing-hauler-h2">Become a Hauler</h2>
            <p className="landing-hauler-body">
              Turn your truck into income. Browse open loads near you, set your own schedule, and get paid fast.
              Thousands of shippers are waiting to work with you.
            </p>
            <ul className="landing-hauler-perks">
              <li>Keep 90% of every payout</li>
              <li>Choose your own routes &amp; hours</li>
              <li>Weekly direct deposits</li>
            </ul>
          </div>
          <div className="landing-hauler-action">
            <Link to="/signup?role=hauler" className="hh-btn hh-btn--accent landing-hauler-btn">
              Start hauling today
            </Link>
            <Link to="/login" className="hh-btn landing-hauler-login-btn">
              Already a hauler? Log in
            </Link>
            <p className="landing-hauler-sub">Free to join &middot; Approval in 24 hrs</p>
          </div>
        </div>
      </section>

      {/* ── Features ── */}
      <section className="landing-section landing-container">
        <div className="landing-section-header">
          <h2 className="landing-section-h2">Everything you need to move freight</h2>
          <p className="landing-section-sub">Built for shippers who want reliability without the red tape.</p>
        </div>
        <div className="landing-features-grid">
          {FEATURES.map((f) => (
            <div key={f.title} className="landing-feature-card">
              <div className="landing-feature-icon">{f.icon}</div>
              <h3 className="landing-feature-h3">{f.title}</h3>
              <p className="landing-feature-body">{f.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── How it works ── */}
      <section className="landing-section landing-how-bg">
        <div className="landing-container">
          <div className="landing-section-header">
            <h2 className="landing-section-h2">How it works</h2>
            <p className="landing-section-sub">From post to delivery in four simple steps.</p>
          </div>
          <div className="landing-steps">
            {STEPS.map((s) => (
              <div key={s.num} className="landing-step">
                <span className="landing-step-num">{s.num}</span>
                <h3 className="landing-step-title">{s.title}</h3>
                <p className="landing-step-body">{s.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Bottom CTA ── */}
      <section className="landing-section landing-container landing-bottom-cta">
        <h2 className="landing-bottom-h2">Ready to move your first load?</h2>
        <p className="landing-bottom-sub">Join thousands of shippers who trust Haul Hub every day.</p>
        <div className="landing-hero-cta">
          <Link to="/signup" className="hh-btn hh-btn--accent landing-cta-primary">
            Get started free
          </Link>
          <Link to="/login" className="hh-btn hh-btn--outline landing-cta-secondary">
            Log in
          </Link>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="landing-footer">
        <div className="landing-container landing-footer-inner">
          <div className="landing-brand">
            <span className="landing-brand-mark">
              <TruckIcon size={16} />
            </span>
            <span className="landing-brand-name" style={{ fontSize: 14 }}>Haul Hub</span>
          </div>
          <p className="landing-footer-copy">&copy; {new Date().getFullYear()} Haul Hub. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
