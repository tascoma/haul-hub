# Haul Hub — Roadmap

Generated 2026-05-26 from a scan of `backend/`, `frontend/`, `ios/`, tests, and migrations.

This is a punch list of what's missing or partially built, grouped into phases by priority and ordered by what unblocks the next phase. Items map to concrete file paths where the work belongs.

---

## Status snapshot

**Working end-to-end today:**
- Auth: signup/login with JWT bearer + bcrypt ([backend/app/routes/auth.py](backend/app/routes/auth.py), [ios/HaulHub/Core/AuthSession.swift](ios/HaulHub/Core/AuthSession.swift), [frontend/src/lib/auth.tsx](frontend/src/lib/auth.tsx))
- Onboarding flow (profile → hauler profile → vehicle → service area) on web and iOS
- Load lifecycle state machine ([backend/app/services/booking.py](backend/app/services/booking.py)) with booking events
- Stripe Connect onboarding link generation (bookkeeping-only mode when keys absent)
- 43 backend tests passing
- Web: shipper + hauler dashboards, post load, browse, detail, profile, vehicle manager
- iOS: hauler Loads/Active/Profile, shipper Home/Post/Tracking/LoadDetail/Profile

**Known deferred / placeholder code:**
- `services/payments.py:93` — `PaymentIntent` creation skipped until shipper has saved PaymentMethod
- `ios/HaulHub/Features/MainTabView.swift` — Earnings and Alerts (×2) tabs are still `placeholder()` (Post a load and Tracking now shipped in Phase 1)
- `ios/HaulHub/Models/MockData.swift` — file marked as deletable placeholder
- `LoadStatus.bidding`, `LoadStatus.disputed`, `PricingMode.customer_offer`, `PricingMode.open_bidding` defined but no routes drive these states

---

## Phase 1 — Close the iOS shipper loop ✅ Done (2026-05-27)

Goal: shipper can post a load and watch it move through delivery on iOS, matching what already works on web.

- [x] **Post-load screen (iOS)** — replaced the placeholder with [PostLoadView.swift](ios/HaulHub/Features/PostLoadView.swift), wired into [MainTabView.swift:57](ios/HaulHub/Features/MainTabView.swift#L57). Submits via new `LoadsClient.createLoad(...)`. Distance is auto-routed from the addresses (MapKit) rather than typed — see [RouteDistance.swift](ios/HaulHub/Core/RouteDistance.swift).
- [x] **Tracking screen (iOS)** — [ShipperTrackingView.swift](ios/HaulHub/Features/ShipperTrackingView.swift) at [MainTabView.swift:61](ios/HaulHub/Features/MainTabView.swift#L61); lists the shipper's loads from `GET /api/me/loads` with lifecycle stages from booking events.
- [x] **`GET /api/loads/{id}/events`** — booking timeline endpoint at [loads.py:299](backend/app/routes/loads.py#L299), restricted to the shipper or assigned hauler.
- [x] **iOS shipper LoadDetail** — [ShipperLoadDetailView.swift](ios/HaulHub/Features/ShipperLoadDetailView.swift), routed from the tracking list.
- [x] **Backend tests for `/events` endpoint** — [backend/tests/test_loads_events.py](backend/tests/test_loads_events.py) (5 tests).

---

## Phase 2 — Real payments (turn off bookkeeping-only mode)

Goal: real money moves on delivery. Required before any pilot with real shippers.

- [ ] **"Save card" flow (web)** — Stripe Elements component on shipper signup or first post-load. Creates a `stripe.Customer` + `PaymentMethod`, persists `stripe_customer_id` on `UserProfile` (column already exists, [user.py:100](backend/app/models/user.py#L100)).
- [ ] **"Save card" flow (iOS)** — `STPPaymentSheet` integration; same persistence on `UserProfile`.
- [ ] **Resolve `services/payments.py:93` TODO** — create real `PaymentIntent` (manual capture) in `authorize_payment_for_load` once shipper has a saved PM. Currently logs and skips.
- [ ] **Payment status UI** — web Load Detail + iOS Active Haul should show "authorized / captured / transferred" from `GET /api/loads/{id}/payment` (route exists at [loads.py:275](backend/app/routes/loads.py#L275); not consumed by any UI).
- [ ] **Expand webhook handlers** ([backend/app/routes/webhooks.py](backend/app/routes/webhooks.py)) — currently only `account.updated` (no-op) and `payment_intent.succeeded`. Add `payment_intent.payment_failed`, `transfer.created`, `charge.refunded`, `account.application.deauthorized`.
- [ ] **Stripe Connect dashboard link** — give haulers a "Manage payouts" link from their profile to their Express dashboard.
- [ ] **Backend tests:** real PaymentIntent path with mocked `stripe` module; webhook handlers for each new event type. Current payments tests cover the 503/bookkeeping paths only.

---

## Phase 3 — Trust & verification (must-have before opening hauler signup)

Goal: don't let unverified haulers accept real-money loads.

- [ ] **Gate `accept_load` on verification** — [booking.py:58](backend/app/services/booking.py#L58) should check `hauler.hauler_profile.verified_at IS NOT NULL`. Currently any hauler with role enabled can accept.
- [ ] **Document upload flow** — `POST /api/me/documents` exists ([me.py:457](backend/app/routes/me.py#L457)) but no UI on web or iOS uploads files. Wire to the Photo upload pattern at [loads.py:297](backend/app/routes/loads.py#L297).
- [ ] **Admin review interface** — minimal: a single page (or CLI script) that lists pending `HaulerDocument` and `IdentityVerification` rows and lets an admin mark them `reviewed_at` + `approved`. Needs `is_admin` flag on `UserProfile` and an admin-only dependency.
- [ ] **Email verification flow** — `email_verified_at` column exists, no flow. Send a token, accept it at `POST /api/auth/verify-email`.
- [ ] **Phone verification (SMS OTP)** — `phone_verified_at` column exists, no flow. Pick a provider (Twilio Verify is easiest); add `POST /api/auth/phone/start` + `/verify`.
- [ ] **Password reset** — `POST /api/auth/forgot-password` + `/reset-password` using single-use tokens.

---

## Phase 4 — Matching & discovery (unlock organic demand→supply)

Goal: posted loads find the right hauler without the hauler manually browsing.

- [ ] **Service-area filtering on browse** — `GET /api/loads` ([loads.py:102](backend/app/routes/loads.py#L102)) returns *every* posted load. Should restrict to loads whose pickup falls inside the hauler's `service_radius_miles` of `home_base_address_id`. PostGIS is installed ([alembic 0005](backend/alembic/versions/0005_postgres_postgis_setup.py)) but unused.
- [ ] **Geocode addresses on create** — `Address` rows have no lat/lon. Add columns + a geocoding call (Mapbox, Google, or Nominatim) in `services/addresses.find_or_create_address`. Without this, distance/radius queries are impossible.
- [ ] **Auto-calculate `estimated_distance_miles`** — iOS now derives it client-side by routing pickup→dropoff with MapKit ([RouteDistance.swift](ios/HaulHub/Core/RouteDistance.swift), Phase 1). Web still has the shipper type it ([PostLoadPage.tsx](frontend/src/pages/PostLoadPage.tsx)); once addresses are geocoded server-side, move this to the backend so web and iOS share one source of truth and pricing stays accurate.
- [ ] **Notify matching haulers when a load is posted** — push to iOS, email/in-app to web (depends on Phase 5 notifications infra).
- [ ] **Search filters on browse** — by date window, weight, urgency, dropoff_kind. UI exists with a search box but only `city`/`state` query params are honored server-side.

---

## Phase 5 — Notifications & realtime

Goal: replace "pull to refresh" with proactive updates; fill the iOS "Alerts" tabs.

- [ ] **Notification model + table** — `Notification(user_id, kind, payload, read_at, created_at)`. New migration, model, schema.
- [ ] **`GET /api/me/notifications` + `PATCH /api/me/notifications/{id}/read`** — fill the iOS Alerts tabs ([MainTabView.swift:44, :65](ios/HaulHub/Features/MainTabView.swift#L44)) and add a web inbox.
- [ ] **Emit notifications from booking transitions** — wire from [booking.py](backend/app/services/booking.py): shipper notified on accept/pickup/in_transit/delivered/cancel; hauler notified when their service area gets a new posted load.
- [ ] **APNs push (iOS)** — register device token on login, store in new `DeviceToken` table, send via `aioapns` from the notification dispatcher.
- [ ] **Web push or polling** — start with polling on the Alerts page; upgrade to SSE/WebSocket later if needed.
- [ ] **Live location for in-transit loads** — new `POST /api/loads/{id}/location` from the assigned hauler (rate-limited); shipper tracking page subscribes via polling or WebSocket.

---

## Phase 6 — Ratings, disputes, and lifecycle completion

Goal: close the post-delivery loop and handle when things go wrong.

- [ ] **Rating model + endpoints** — `HaulerProfile.rating_avg`, `rating_count`, `jobs_completed` exist ([user.py:130-132](backend/app/models/user.py#L130)) but are never written. Add `Rating(load_id, rater_user_id, ratee_user_id, stars, comment)`, `POST /api/loads/{id}/rating` post-delivery, and a denormalizing trigger or service that updates the profile aggregates.
- [ ] **Dispute flow** — `LoadStatus.disputed` exists ([load.py:36](backend/app/models/load.py#L36)) with no route. Add `POST /api/loads/{id}/dispute` (either party, post-pickup, pre/post delivery) and admin dispute resolution endpoints.
- [ ] **Bidding mode** — `LoadStatus.bidding` + `PricingMode.open_bidding` defined but unimplemented. New `Bid` model + `POST /api/loads/{id}/bids`, `POST /api/loads/{id}/bids/{bid_id}/accept`.
- [ ] **Customer offer mode** — `PricingMode.customer_offer` lets shipper name a price; hauler accepts as-is. Add to post-load flow + accept transitions.

---

## Phase 7 — Operations, CI, and quality

Goal: ship safely and recover from mistakes.

- [ ] **GitHub Actions CI** — no `.github/` directory exists. Add: lint + pytest on PR to `dev` / `main`, auto-deploy backend + frontend to Render staging on `dev` merge, production on `main` merge. The `/setup-ci` skill exists; run it.
- [ ] **Frontend tests** — Vitest + React Testing Library. None exist. Start with the API client and the role-routing logic in [App.tsx:23-42](frontend/src/App.tsx#L23-L42).
- [ ] **iOS tests** — `HaulHubTests/` directory exists but is empty. Start with `AuthSession` phase transitions and `LoadsClient` request shaping.
- [ ] **Backend test gaps** — missing coverage for service areas, hauler documents, identity verifications, terms acceptances, address CRUD on `me` router, password change happy path.
- [ ] **Rate limiting** — add `slowapi` or similar on `/api/auth/*` and `/api/loads/{id}/location` (when added in Phase 5).
- [ ] **JWT refresh tokens** — current token is single 7-day bearer with no rotation or revocation. Add refresh + revocation list for compromised tokens.
- [ ] **Admin user-suspend endpoint** — `UserStatus.suspended` exists ([user.py:29](backend/app/models/user.py#L29)) but no path can set it.
- [ ] **Update `.env.example`** — missing all `STRIPE_*` and `PRICE_*` variables currently in `core/config.py`.
- [ ] **Rename leftover template references** — `README.md` line 24 still says `agent-webapp-template`; `backend/app/agents/agent.py` is the unmodified sample agent and isn't wired to any route. Decide: wire it up (chat support / smart pricing) or remove.

---

## Phase 8 — Nice-to-haves

- [ ] **Agent-driven smart pricing** — use [agents/agent.py](backend/app/agents/agent.py) (Pydantic-AI is already a dependency) to suggest a price from item description + photos, presented in `PostLoadPage` as "AI suggested: $X".
- [ ] **Saved searches** for haulers (e.g. "any load over $200 within 30mi of home").
- [ ] **Multi-stop loads** — current `Load` has one pickup + one dropoff; some moves are sequential.
- [ ] **Shipper "favorite haulers"** — `LoadVisibility.invite_only` is defined ([load.py:56](backend/app/models/load.py#L56)) but no UI sends invites.
- [ ] **Receipts (PDF)** — generate on delivery, email to shipper.
- [ ] **iOS Earnings tab** — replace `placeholder(title: "Earnings")` ([MainTabView.swift:40](ios/HaulHub/Features/MainTabView.swift#L40)) with payouts list once Phase 2 is done.
- [ ] **Analytics / events** — minimal product analytics so we can see funnel drop-off in onboarding and posting.

---

## Cross-cutting tech debt to address opportunistically

- `Load` keeps both flat address columns *and* `pickup_address_id` / `dropoff_address_id` FKs ([load.py:94](backend/app/models/load.py#L94) "kept for frontend compatibility"). After Phase 4 geocoding lands, plan a deprecation of the flat columns.
- `frontend/src/pages/DashboardPage.tsx` (233 lines) appears unused — `App.tsx` only routes `/dashboard` → `DashboardRedirect`. Confirm and delete.
- `ios/HaulHub/Models/MockData.swift` — self-marked as deletable placeholder.
- `services/storage.py` is a local-filesystem fallback; production needs the Supabase Storage version (the `/setup-storage` skill exists).
