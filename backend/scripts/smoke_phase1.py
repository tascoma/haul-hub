"""Smoke test for Phase 1 auth + profile endpoints. Run from backend/:
    uv run python scripts/smoke_phase1.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.main import app  # noqa: E402


async def main() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Signup
        r = await client.post(
            "/api/auth/signup",
            json={"email": "alice@example.com", "password": "supersecret", "full_name": "Alice"},
        )
        assert r.status_code == 201, r.text
        token = r.json()["access_token"]
        auth = {"Authorization": f"Bearer {token}"}
        print("signup ok, token len:", len(token))

        # Duplicate signup should 409
        r = await client.post(
            "/api/auth/signup",
            json={"email": "alice@example.com", "password": "supersecret"},
        )
        assert r.status_code == 409, r.text
        print("duplicate signup -> 409 ok")

        # Login
        r = await client.post(
            "/api/auth/login",
            json={"email": "alice@example.com", "password": "supersecret"},
        )
        assert r.status_code == 200, r.text
        print("login ok")

        # GET /api/me
        r = await client.get("/api/me", headers=auth)
        assert r.status_code == 200, r.text
        me = r.json()
        assert me["email"] == "alice@example.com"
        assert me["profile"]["shipper_enabled"] is True
        assert me["profile"]["hauler_enabled"] is False
        print("get me ok:", me["email"], "shipper:", me["profile"]["shipper_enabled"])

        # PATCH /api/me
        r = await client.patch("/api/me", json={"phone": "+15551234567"}, headers=auth)
        assert r.status_code == 200, r.text
        assert r.json()["profile"]["phone"] == "+15551234567"
        print("patch me ok")

        # Hauler profile not yet enabled
        r = await client.get("/api/me/hauler-profile", headers=auth)
        assert r.status_code == 404, r.text
        print("no hauler profile -> 404 ok")

        # Enable hauler
        r = await client.post(
            "/api/me/enable-hauler",
            json={"vehicle_type": "pickup_with_trailer", "max_weight_lbs": 10000},
            headers=auth,
        )
        assert r.status_code == 201, r.text
        print("enable hauler ok:", r.json()["vehicle_type"])

        # Now hauler-enabled
        r = await client.get("/api/me", headers=auth)
        assert r.json()["profile"]["hauler_enabled"] is True
        print("me.hauler_enabled flipped to True")

        # GET hauler profile
        r = await client.get("/api/me/hauler-profile", headers=auth)
        assert r.status_code == 200, r.text
        assert r.json()["max_weight_lbs"] == 10000
        print("get hauler profile ok")

        # Enabling again should 409
        r = await client.post(
            "/api/me/enable-hauler",
            json={"vehicle_type": "pickup"},
            headers=auth,
        )
        assert r.status_code == 409, r.text
        print("re-enable hauler -> 409 ok")

        # No token → 401
        r = await client.get("/api/me")
        assert r.status_code == 401, r.text
        print("unauthenticated -> 401 ok")

        # Bad token → 401
        r = await client.get("/api/me", headers={"Authorization": "Bearer not.a.token"})
        assert r.status_code == 401, r.text
        print("bad token -> 401 ok")

    print("\nAll Phase 1 checks passed.")


if __name__ == "__main__":
    asyncio.run(main())
