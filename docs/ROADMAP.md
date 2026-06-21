# Haul Hub — Roadmap

Last updated 2026-06-06. Previous scan was 2026-05-26; this revision incorporates PRs #2–#6 and the Stripe payments work (web + iOS) now in the working tree.

This is a punch list of what's missing or partially built, grouped into phases by priority and ordered by what unblocks the next phase. Items map to concrete file paths where the work belongs.

---

## Status snapshot

**Working end-to-end today:**
- Auth: signup/login with JWT bearer + bcrypt ([backend/app/routes/auth.py](backend/app/routes/auth.py), [ios/HaulHub/Core/AuthSession.swift](ios/HaulHub/Core/AuthSession.swift), [frontend/src/lib/auth.tsx](frontend/src/lib/auth.tsx))
- Onboarding flow (profile → hauler profile → vehicle → service area) on web and iOS
- Load lifecycle state machine ([backend/app/services/booking.py](backend/app/services/booking.py)) with booking events
- Stripe payments wired end-to-end (see Phase 3): hauler Connect onboarding, shipper card setup, and the authorize-on-accept → capture+transfer-on-deliver → refund-on-cancel flow on both web and iOS. Falls back to bookkeeping-only mode when keys are absent.
- **53 backend tests passing** (was 43 — see Phase 4 completions below); **7 iOS tests passing** (payment models/client + config)
- Web: shipper + hauler dashboards, post load, browse + pickups map, load detail with route map + payment status, profile, vehicle manager, payment method + billing address
- iOS: hauler Loads/Active/Profile, shipper Home/Post/Tracking/LoadDetail/Profile with real route maps, payment status on load details, shipper card setup (PaymentSheet), hauler Connect onboarding
- Backend serves the compiled React frontend from its root (no separate static hosting required for staging)
- Pickup/dropoff addresses geocoded on load create via Google Maps API; hauler service-radius filtering live on `GET /api/loads?near_me=true`

**Known deferred / placeholder code:**
- `ios/HaulHub/Features/MainTabView.swift:40,44,65` — Earnings and Alerts (×2) tabs are still `placeholder()`
- `ios/HaulHub/Models/MockData.swift` — file marked as deletable placeholder
- `LoadStatus.bidding`, `LoadStatus.disputed`, `PricingMode.customer_offer`, `PricingMode.open_bidding` defined but no routes drive these states
- `frontend/src/pages/DashboardPage.tsx` — confirmed unused; `App.tsx` never imports it directly, only `DashboardRedirect`, `ShipperDashboardPage`, and `HaulerDashboardPage` are used

---

## Phase 1 — Close the iOS shipper loop ✅ Done (2026-05-27)

Goal: shipper can post a load and watch it move through delivery on iOS, matching what already works on web.

- [x] **Post-load screen (iOS)** — replaced the placeholder with [PostLoadView.swift](ios/HaulHub/Features/PostLoadView.swift), wired into [MainTabView.swift:57](ios/HaulHub/Features/MainTabView.swift#L57). Submits via new `LoadsClient.createLoad(...)`. Distance is auto-routed from the addresses (MapKit) rather than typed — see [RouteDistance.swift](ios/HaulHub/Core/RouteDistance.swift).
- [x] **Tracking screen (iOS)** — [ShipperTrackingView.swift](ios/HaulHub/Features/ShipperTrackingView.swift) at [MainTabView.swift:61](ios/HaulHub/Features/MainTabView.swift#L61); lists the shipper's loads from `GET /api/me/loads` with lifecycle stages from booking events.
- [x] **`GET /api/loads/{id}/events`** — booking timeline endpoint at [loads.py:299](backend/app/routes/loads.py#L299), restricted to the shipper or assigned hauler.
- [x] **iOS shipper LoadDetail** — [ShipperLoadDetailView.swift](ios/HaulHub/Features/ShipperLoadDetailView.swift), routed from the tracking list.
- [x] **Backend tests for `/events` endpoint** — [backend/tests/test_loads_events.py](backend/tests/test_loads_events.py) (5 tests).

---

## Phase 2 — Maps & geocoding ✅ Done (2026-06-06)

Goal: addresses carry coordinates so routes can be displayed and haulers only see loads in their area.

- [x] **Geocode addresses on create** — `services/geocoding.py` calls the Google Maps Geocoding API in `find_or_create_address` when `geocode_if_missing=True`. Failures are silently tolerated (no coordinates stored); the key is in `.env.example` as `GOOGLE_MAPS_API_KEY`.
- [x] **Service-area filtering on browse** — `_filter_within_service_radius` in [loads.py:129](backend/app/routes/loads.py#L129) uses Haversine math ([addresses.py:19](backend/app/services/addresses.py#L19)); `GET /api/loads?near_me=true` restricts results to loads whose pickup falls within the hauler's `service_radius_miles` of `home_base_address_id`. PostGIS geom column (migration 0008) stays reserved for future index-backed spatial queries.
- [x] **Route map on web load detail** — [RouteMap.tsx](frontend/src/components/RouteMap.tsx) renders a Google Maps route between pickup and dropoff on [LoadDetailPage.tsx](frontend/src/pages/LoadDetailPage.tsx).
- [x] **Pickups map on web browse** — [PickupsMap.tsx](frontend/src/components/PickupsMap.tsx) shows all posted load pickups as pins on [BrowseLoadsPage.tsx](frontend/src/pages/BrowseLoadsPage.tsx).
- [x] **Route map on iOS load detail** — real MapKit route shown in both [LoadDetailView.swift](ios/HaulHub/Features/LoadDetailView.swift) and [ShipperLoadDetailView.swift](ios/HaulHub/Features/ShipperLoadDetailView.swift) via [RouteDistance.swift](ios/HaulHub/Core/RouteDistance.swift).
- [x] **Geocoding tests** — [test_geocoding.py](backend/tests/test_geocoding.py), [test_loads_address_normalization.py](backend/tests/test_loads_address_normalization.py), and `near_me` coverage in [test_loads.py:227](backend/tests/test_loads.py#L227).

---

## Phase 3 — Real payments 🚧 Mostly done (2026-06-06)

Goal: real money moves on delivery. Required before any pilot with real shippers. Core flow is wired on web and iOS; what's left is webhook breadth and real-Stripe test coverage.

- [x] **"Save card" flow (web)** — [PaymentMethodPage.tsx](frontend/src/pages/PaymentMethodPage.tsx) uses Stripe Elements `confirmCardSetup` off a SetupIntent, attaches the PaymentMethod, and sets it as the customer default. Persists `stripe_customer_id` / `stripe_default_payment_method_id` on `UserProfile`.
- [x] **"Save card" flow (iOS)** — [PaymentMethodView.swift](ios/HaulHub/Features/PaymentMethodView.swift) presents Stripe **PaymentSheet** in SetupIntent mode, retrieves the confirmed SetupIntent to recover the PaymentMethod id, then `POST /api/me/payment-method`. SDK added via SPM in [project.yml](ios/project.yml).
- [x] **Real `PaymentIntent` on accept** — `authorize_payment_for_load` ([services/payments.py](backend/app/services/payments.py)) creates a manual-capture `PaymentIntent` with `application_fee_amount` + `transfer_data` when the shipper has a saved PM and the hauler is Connect-onboarded; `capture_and_transfer` on deliver, `refund_on_cancel` on cancel. Falls back to bookkeeping rows when keys/PM are absent.
- [x] **Payment status UI** — web [LoadDetailPage.tsx](frontend/src/pages/LoadDetailPage.tsx) and iOS [PaymentStatusCard.swift](ios/HaulHub/Features/PaymentStatusCard.swift) (on hauler [LoadDetailView](ios/HaulHub/Features/LoadDetailView.swift) + shipper [ShipperLoadDetailView](ios/HaulHub/Features/ShipperLoadDetailView.swift)) consume `GET /api/loads/{id}/payment` and show authorized / captured / transferred / refunded.
- [x] **Stripe Connect onboarding + manage link** — web [ProfilePage.tsx](frontend/src/pages/ProfilePage.tsx) and iOS [ProfileView.swift](ios/HaulHub/Features/ProfileView.swift) "Connect / Manage Stripe account" generate a hosted Express AccountLink; iOS opens it in [SafariView.swift](ios/HaulHub/Core/SafariView.swift) and refreshes Connect status on return.
- [x] **Add Stripe vars to `.env.example`** — `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_CONNECT_REFRESH_URL`, `STRIPE_CONNECT_RETURN_URL`, `PLATFORM_FEE_BPS` in backend `.env.example`; `VITE_STRIPE_PUBLISHABLE_KEY` + `VITE_PLATFORM_FEE_BPS` in frontend `.env.example`. iOS reads `STRIPE_PUBLISHABLE_KEY` via [Config.swift](ios/HaulHub/Core/Config.swift).
- [~] **Webhook handlers** ([backend/app/routes/webhooks.py](backend/app/routes/webhooks.py)) — `account.updated`, `payment_intent.succeeded`, and `payment_intent.payment_failed` are handled. Still to add: `transfer.created`, `charge.refunded`, `account.application.deauthorized` (and `account.updated` is currently a no-op — it should persist Connect capability/`charges_enabled` status onto the hauler profile).
- [ ] **Backend tests for the real-Stripe path** — current [test_payments.py](backend/tests/test_payments.py) (8 tests) covers the bookkeeping/503 lifecycle and the `payment_intent.payment_failed` webhook. Add a mocked-`stripe` test that asserts the real `PaymentIntent` create/capture/transfer/refund calls and arguments, plus coverage for the new webhook events above.

---

## Phase 4 — Trust & verification (must-have before opening hauler signup)

Goal: don't let unverified haulers accept real-money loads.

- [ ] **Gate `accept_load` on verification** — [booking.py:58](backend/app/services/booking.py#L58) should check `hauler.hauler_profile.verified_at IS NOT NULL`. Currently any hauler with role enabled can accept.
- [ ] **Document upload flow** — `POST /api/me/documents` exists ([me.py](backend/app/routes/me.py)) but no UI on web or iOS uploads files. Wire to the photo upload pattern at [loads.py:358](backend/app/routes/loads.py#L358).
- [ ] **Admin review interface** — minimal: a single page (or CLI script) that lists pending `HaulerDocument` and `IdentityVerification` rows and lets an admin mark them `reviewed_at` + `approved`. Needs `is_admin` flag on `UserProfile` and an admin-only dependency.
- [ ] **Email verification flow** — `email_verified_at` column exists, no flow. Send a token, accept it at `POST /api/auth/verify-email`.
- [ ] **Phone verification (SMS OTP)** — `phone_verified_at` column exists, no flow. Pick a provider (Twilio Verify is easiest); add `POST /api/auth/phone/start` + `/verify`.
- [ ] **Password reset** — `POST /api/auth/forgot-password` + `/reset-password` using single-use tokens.

---

## Phase 5 — Matching & discovery (unlock organic demand→supply)

Goal: posted loads find the right hauler without them manually browsing.

- [ ] **Auto-calculate `estimated_distance_miles` on web** — iOS derives it client-side via MapKit ([RouteDistance.swift](ios/HaulHub/Core/RouteDistance.swift)). Web [PostLoadPage.tsx](frontend/src/pages/PostLoadPage.tsx) still requires the shipper to type the distance manually. Once the backend geocodes both addresses, derive the distance server-side so web and iOS share one source of truth and pricing stays accurate.
- [ ] **Notify matching haulers when a load is posted** — push to iOS, email/in-app to web (depends on Phase 6 notifications infra). After geocoding is in place the server knows which haulers' service areas overlap the pickup.
- [ ] **Search filters on browse** — filter by date window, weight, urgency, `dropoff_kind`. The web browse UI has a search box but only `city`/`state` query params are honored server-side ([loads.py:107](backend/app/routes/loads.py#L107)).

---

## Phase 6 — Notifications & realtime

Goal: replace "pull to refresh" with proactive updates; fill the iOS "Alerts" tabs.

- [ ] **Notification model + table** — `Notification(user_id, kind, payload, read_at, created_at)`. New migration, model, schema.
- [ ] **`GET /api/me/notifications` + `PATCH /api/me/notifications/{id}/read`** — fill the iOS Alerts tabs ([MainTabView.swift:44, :65](ios/HaulHub/Features/MainTabView.swift#L44)) and add a web inbox.
- [ ] **Emit notifications from booking transitions** — wire from [booking.py](backend/app/services/booking.py): shipper notified on accept/pickup/in_transit/delivered/cancel; hauler notified when their service area gets a new posted load.
- [ ] **APNs push (iOS)** — register device token on login, store in new `DeviceToken` table, send via `aioapns` from the notification dispatcher.
- [ ] **Web push or polling** — start with polling on the Alerts page; upgrade to SSE/WebSocket later if needed.
- [ ] **Live location for in-transit loads** — new `POST /api/loads/{id}/location` from the assigned hauler (rate-limited); shipper tracking page subscribes via polling or WebSocket.

---

## Phase 7 — Ratings, disputes, and lifecycle completion

Goal: close the post-delivery loop and handle when things go wrong.

- [ ] **Rating model + endpoints** — `HaulerProfile.rating_avg`, `rating_count`, `jobs_completed` exist ([user.py:130-132](backend/app/models/user.py#L130)) but are never written. Add `Rating(load_id, rater_user_id, ratee_user_id, stars, comment)`, `POST /api/loads/{id}/rating` post-delivery, and a denormalizing trigger or service that updates the profile aggregates.
- [ ] **Dispute flow** — `LoadStatus.disputed` exists ([load.py:36](backend/app/models/load.py#L36)) with no route. Add `POST /api/loads/{id}/dispute` (either party, post-pickup, pre/post delivery) and admin dispute resolution endpoints.
- [ ] **Bidding mode** — `LoadStatus.bidding` + `PricingMode.open_bidding` defined but unimplemented. New `Bid` model + `POST /api/loads/{id}/bids`, `POST /api/loads/{id}/bids/{bid_id}/accept`.
- [ ] **Customer offer mode** — `PricingMode.customer_offer` lets shipper name a price; hauler accepts as-is. Add to post-load flow + accept transitions.

---

## Phase 8 — Operations, CI, and quality

Goal: ship safely and recover from mistakes.

- [ ] **GitHub Actions CI** — no `.github/` directory exists. Add: lint + pytest on PR to `dev` / `main`, auto-deploy backend + frontend to Render staging on `dev` merge, production on `main` merge. The `/setup-ci` skill exists; run it.
- [ ] **Frontend tests** — Vitest + React Testing Library. None exist. Start with the API client and the role-routing logic in [App.tsx:36-42](frontend/src/App.tsx#L36).
- [ ] **iOS tests** — [PaymentModelsTests.swift](ios/HaulHubTests/PaymentModelsTests.swift) covers `PaymentsClient` decoding + 404→nil mapping via a `URLProtocol` stub (good harness to reuse). Still missing: `AuthSession` phase transitions and `LoadsClient` request shaping.
- [ ] **Backend test gaps** — missing coverage for service areas, hauler documents, identity verifications, terms acceptances, address CRUD on `me` router, password change happy path.
- [ ] **Rate limiting** — add `slowapi` or similar on `/api/auth/*` and `/api/loads/{id}/location` (when added in Phase 6).
- [ ] **JWT refresh tokens** — current token is single 7-day bearer with no rotation or revocation. Add refresh + revocation list for compromised tokens.
- [ ] **Admin user-suspend endpoint** — `UserStatus.suspended` exists ([user.py:29](backend/app/models/user.py#L29)) but no path can set it.
- [ ] **Clean up leftover template artifacts** — `README.md` lines 3 and 23–24 still reference `agent-webapp-template`; `backend/app/agents/agent.py` is the unmodified sample agent, wired to no route. Decide: wire it (chat support / smart pricing) or remove it.

---

## Phase 9 — Nice-to-haves

- [ ] **Agent-driven smart pricing** — use [agents/agent.py](backend/app/agents/agent.py) (Pydantic-AI is already a dependency) to suggest a price from item description + photos, presented in `PostLoadPage` as "AI suggested: $X".
- [ ] **Saved searches** for haulers (e.g. "any load over $200 within 30mi of home").
- [ ] **Multi-stop loads** — current `Load` has one pickup + one dropoff; some moves are sequential.
- [ ] **Shipper "favorite haulers"** — `LoadVisibility.invite_only` is defined ([load.py:56](backend/app/models/load.py#L56)) but no UI sends invites.
- [ ] **Receipts (PDF)** — generate on delivery, email to shipper.
- [ ] **iOS Earnings tab** — replace `placeholder(title: "Earnings")` ([MainTabView.swift:40](ios/HaulHub/Features/MainTabView.swift#L40)) with payouts list once Phase 3 is done.
- [ ] **Analytics / events** — minimal product analytics so we can see funnel drop-off in onboarding and posting.

---

## Cross-cutting tech debt to address opportunistically

- `Load` keeps both flat address columns *and* `pickup_address_id` / `dropoff_address_id` FKs ([load.py:94](backend/app/models/load.py#L94), comment: "kept for frontend compatibility"). After Phase 5 server-side distance calculation lands, plan a deprecation of the flat columns and a migration to drop them.
- `frontend/src/pages/DashboardPage.tsx` — confirmed unused. `App.tsx` routes `/dashboard` → `DashboardRedirect` which redirects to the role-specific dashboard; `DashboardPage.tsx` itself is never imported. Safe to delete.
- `ios/HaulHub/Models/MockData.swift` — self-marked as deletable placeholder.
- `services/storage.py` is a local-filesystem fallback; production needs the Supabase Storage version (the `/setup-storage` skill exists).
