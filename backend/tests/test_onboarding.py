"""Onboarding flow: signup roles, idempotent enable-hauler, status transitions."""

from httpx import AsyncClient


async def _signup(client: AsyncClient, email: str, **extra) -> dict:
    body = {"email": email, "password": "supersecret", **extra}
    r = await client.post("/api/auth/signup", json=body)
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


async def test_signup_default_role_is_customer(client: AsyncClient) -> None:
    auth = await _signup(client, "default@example.com")
    me = (await client.get("/api/me", headers=auth)).json()
    assert me["profile"]["shipper_enabled"] is True
    assert me["profile"]["hauler_enabled"] is False


async def test_signup_as_hauler_only(client: AsyncClient) -> None:
    auth = await _signup(client, "hauler@example.com", roles=["hauler"])
    me = (await client.get("/api/me", headers=auth)).json()
    assert me["profile"]["shipper_enabled"] is False
    assert me["profile"]["hauler_enabled"] is True

    # HaulerProfile was created in the same transaction
    r = await client.get("/api/me/hauler-profile", headers=auth)
    assert r.status_code == 200, r.text


async def test_signup_as_both_roles(client: AsyncClient) -> None:
    auth = await _signup(client, "both@example.com", roles=["customer", "hauler"])
    me = (await client.get("/api/me", headers=auth)).json()
    assert me["profile"]["shipper_enabled"] is True
    assert me["profile"]["hauler_enabled"] is True


async def test_signup_empty_roles_rejected(client: AsyncClient) -> None:
    r = await client.post(
        "/api/auth/signup",
        json={"email": "none@example.com", "password": "supersecret", "roles": []},
    )
    assert r.status_code == 422, r.text


async def test_enable_hauler_is_idempotent(client: AsyncClient) -> None:
    auth = await _signup(client, "idem@example.com")

    r = await client.post(
        "/api/me/enable-hauler",
        json={"company_name": "First Try", "service_radius_miles": 50},
        headers=auth,
    )
    assert r.status_code == 201, r.text
    assert r.json()["company_name"] == "First Try"

    # Second call: 200, and does not overwrite existing fields
    r = await client.post(
        "/api/me/enable-hauler",
        json={"company_name": "Second Try"},
        headers=auth,
    )
    assert r.status_code == 200, r.text
    assert r.json()["company_name"] == "First Try"
    assert r.json()["service_radius_miles"] == 50


async def test_onboarding_status_customer_flow(client: AsyncClient) -> None:
    auth = await _signup(client, "cust@example.com")

    status = (await client.get("/api/me/onboarding-status", headers=auth)).json()
    assert status["next_step"] == "profile"
    assert status["customer_ready"] is False
    assert status["hauler_ready"] is False

    # Fill profile (name from signup is missing, phone is missing)
    await client.patch(
        "/api/me",
        json={"full_name": "Cust Omer", "phone": "+15550000001"},
        headers=auth,
    )

    status = (await client.get("/api/me/onboarding-status", headers=auth)).json()
    assert status["next_step"] == "done"
    assert status["customer_ready"] is True
    assert status["hauler_ready"] is False


async def test_onboarding_status_hauler_flow(client: AsyncClient) -> None:
    auth = await _signup(client, "haul@example.com", roles=["hauler"], full_name="H Auler")

    # full_name was set at signup; need phone
    status = (await client.get("/api/me/onboarding-status", headers=auth)).json()
    assert status["next_step"] == "profile"

    await client.patch("/api/me", json={"phone": "+15550000002"}, headers=auth)

    # HaulerProfile already exists (signup created it), so next is vehicle
    status = (await client.get("/api/me/onboarding-status", headers=auth)).json()
    assert status["next_step"] == "hauler_vehicle", status
    assert status["checks"]["has_vehicle"] is False

    # Add a vehicle
    r = await client.post(
        "/api/me/vehicles",
        json={"vehicle_type": "pickup", "is_default": True},
        headers=auth,
    )
    assert r.status_code == 201, r.text

    status = (await client.get("/api/me/onboarding-status", headers=auth)).json()
    assert status["next_step"] == "hauler_service_area"
    assert status["checks"]["has_vehicle"] is True
    assert status["checks"]["has_service_area"] is False

    # Create address and attach to hauler profile as home base
    r = await client.post(
        "/api/me/addresses/raw",
        json={
            "line1": "123 Main St",
            "city": "Portland",
            "state": "OR",
            "postal_code": "97201",
            "country": "US",
        },
        headers=auth,
    )
    assert r.status_code == 201, r.text
    address_id = r.json()["id"]

    r = await client.patch(
        "/api/me/hauler-profile",
        json={"home_base_address_id": address_id, "service_radius_miles": 30},
        headers=auth,
    )
    assert r.status_code == 200, r.text

    status = (await client.get("/api/me/onboarding-status", headers=auth)).json()
    assert status["next_step"] == "hauler_documents"
    assert status["checks"]["has_insurance"] is False
    assert status["checks"]["has_drivers_license"] is False
    assert status["hauler_ready"] is False

    # Upload an insurance certificate
    fake_file = b"fake-pdf-content"
    r = await client.post(
        "/api/me/documents/upload",
        files={"file": ("insurance.pdf", fake_file, "application/pdf")},
        data={"kind": "insurance_certificate", "carrier_name": "ACME Insurance", "policy_number": "POL-001"},
        headers=auth,
    )
    assert r.status_code == 201, r.text

    # Upload a driver's license
    r = await client.post(
        "/api/me/verifications/upload",
        files={"file": ("license.jpg", fake_file, "image/jpeg")},
        data={"kind": "drivers_license"},
        headers=auth,
    )
    assert r.status_code == 201, r.text

    status = (await client.get("/api/me/onboarding-status", headers=auth)).json()
    assert status["next_step"] == "hauler_verification"
    assert status["checks"]["has_insurance"] is True
    assert status["checks"]["has_drivers_license"] is True
    assert status["checks"]["has_background_check"] is False

    # Create a Stripe Identity verification record (pending) via the JSON endpoint
    r = await client.post(
        "/api/me/verifications",
        json={"kind": "stripe_identity", "provider": "stripe", "provider_reference": "vs_test_123"},
        headers=auth,
    )
    assert r.status_code == 201, r.text

    status = (await client.get("/api/me/onboarding-status", headers=auth)).json()
    assert status["next_step"] == "done"
    assert status["hauler_ready"] is True
    assert status["checks"]["has_background_check"] is True


async def test_onboarding_status_dual_role(client: AsyncClient) -> None:
    auth = await _signup(client, "dual@example.com", roles=["customer", "hauler"])

    # Fill profile
    await client.patch(
        "/api/me",
        json={"full_name": "Du Al", "phone": "+15550000003"},
        headers=auth,
    )

    # Customer is ready; hauler still needs vehicle + service area
    status = (await client.get("/api/me/onboarding-status", headers=auth)).json()
    assert status["customer_ready"] is True
    assert status["hauler_ready"] is False
    assert status["next_step"] == "hauler_vehicle"
