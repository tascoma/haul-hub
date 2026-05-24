"""Smoke test for Phase 2 loads. Run from backend/:
    uv run python scripts/smoke_phase2.py
"""

import asyncio
import io
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.main import app  # noqa: E402
from app.services.pricing import calculate_price_cents  # noqa: E402

from app.models.load import Urgency  # noqa: E402


def _load_payload(suffix: str = "") -> dict:
    now = datetime.now(UTC)
    return {
        "title": f"Pallet of stuff{suffix}",
        "description": "Three pallets, palletized",
        "weight_lbs": 1500,
        "length_ft": 8,
        "width_ft": 4,
        "height_ft": 4,
        "pickup_address": "123 Main St",
        "pickup_city": "Austin",
        "pickup_state": "TX",
        "pickup_zip": "78701",
        "pickup_window_start": (now + timedelta(days=1)).isoformat(),
        "pickup_window_end": (now + timedelta(days=1, hours=4)).isoformat(),
        "dropoff_address": "456 Elm St",
        "dropoff_city": "Dallas",
        "dropoff_state": "TX",
        "dropoff_zip": "75201",
        "dropoff_by": (now + timedelta(days=2)).isoformat(),
        "estimated_distance_miles": 200,
        "urgency": "standard",
    }


async def _signup(client: AsyncClient, email: str) -> str:
    r = await client.post(
        "/api/auth/signup",
        json={"email": email, "password": "supersecret", "full_name": email.split("@")[0]},
    )
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


async def main() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        shipper_token = await _signup(client, "shipper@example.com")
        other_token = await _signup(client, "other@example.com")
        shipper_h = {"Authorization": f"Bearer {shipper_token}"}
        other_h = {"Authorization": f"Bearer {other_token}"}

        # Pricing formula reference
        expected = calculate_price_cents(
            distance_miles=200, weight_lbs=1500, urgency=Urgency.standard
        )
        print("expected std price (cents):", expected)
        assert expected == (
            settings.price_base_cents
            + settings.price_per_mile_cents * 200
            + settings.price_weight_surcharge_per_100lb_cents * 15
        )

        # Create load
        r = await client.post("/api/loads", json=_load_payload(), headers=shipper_h)
        assert r.status_code == 201, r.text
        load = r.json()
        load_id = load["id"]
        assert load["status"] == "posted"
        assert load["calculated_price_cents"] == expected
        print(f"create load ok: {load_id} price={load['calculated_price_cents']}")

        # Express pricing
        express_payload = _load_payload(" (express)") | {"urgency": "express"}
        r = await client.post("/api/loads", json=express_payload, headers=shipper_h)
        assert r.status_code == 201, r.text
        express_price = r.json()["calculated_price_cents"]
        assert express_price > expected
        assert express_price == int(round(expected * settings.price_express_multiplier))
        print(f"express price: {express_price} (> std)")

        # Browse - both should be visible
        r = await client.get("/api/loads", headers=other_h)
        assert r.status_code == 200, r.text
        assert len(r.json()) >= 2
        print(f"list loads ok: {len(r.json())} loads")

        # Filter by city
        r = await client.get("/api/loads?city=Austin", headers=other_h)
        assert r.status_code == 200, r.text
        assert all(l["pickup_city"] == "Austin" for l in r.json())
        print("filter by city ok")

        # Filter by nonexistent city → empty
        r = await client.get("/api/loads?city=Nowhere", headers=other_h)
        assert r.json() == []
        print("filter by missing city -> [] ok")

        # GET detail
        r = await client.get(f"/api/loads/{load_id}", headers=other_h)
        assert r.status_code == 200, r.text
        print("get detail ok")

        # PATCH by owner — recalc price when weight changes
        r = await client.patch(
            f"/api/loads/{load_id}",
            json={"weight_lbs": 3000, "title": "Bigger pallet"},
            headers=shipper_h,
        )
        assert r.status_code == 200, r.text
        updated = r.json()
        recalc = calculate_price_cents(
            distance_miles=200, weight_lbs=3000, urgency=Urgency.standard
        )
        assert updated["weight_lbs"] == 3000
        assert updated["title"] == "Bigger pallet"
        assert updated["calculated_price_cents"] == recalc
        print(f"patch (with price recalc) ok: {updated['calculated_price_cents']}")

        # PATCH by non-owner → 403
        r = await client.patch(
            f"/api/loads/{load_id}", json={"title": "nope"}, headers=other_h
        )
        assert r.status_code == 403, r.text
        print("patch by non-owner -> 403 ok")

        # Photo upload (owner)
        files = {"file": ("test.png", io.BytesIO(b"\x89PNG\r\n\x1a\nfake"), "image/png")}
        r = await client.post(f"/api/loads/{load_id}/photos", files=files, headers=shipper_h)
        assert r.status_code == 200, r.text
        assert len(r.json()["photo_urls"]) == 1
        photo_url = r.json()["photo_urls"][0]
        assert photo_url.startswith("/uploads/loads/")
        print(f"photo upload ok: {photo_url}")

        # Verify file is servable via StaticFiles mount
        r = await client.get(photo_url)
        assert r.status_code == 200, r.text
        assert r.content.startswith(b"\x89PNG")
        print("served photo ok")

        # Photo upload by non-owner → 403
        files = {"file": ("nope.png", io.BytesIO(b"x"), "image/png")}
        r = await client.post(f"/api/loads/{load_id}/photos", files=files, headers=other_h)
        assert r.status_code == 403, r.text
        print("photo upload by non-owner -> 403 ok")

        # DELETE by non-owner → 403
        r = await client.delete(f"/api/loads/{load_id}", headers=other_h)
        assert r.status_code == 403, r.text
        print("delete by non-owner -> 403 ok")

        # DELETE by owner → 204, then list excludes it
        r = await client.delete(f"/api/loads/{load_id}", headers=shipper_h)
        assert r.status_code == 204, r.text
        r = await client.get(f"/api/loads/{load_id}", headers=shipper_h)
        assert r.json()["status"] == "cancelled"
        assert r.json()["cancelled_at"] is not None
        print("cancel ok, status=cancelled")

        # Re-delete cancelled load → 409
        r = await client.delete(f"/api/loads/{load_id}", headers=shipper_h)
        assert r.status_code == 409, r.text
        print("re-cancel -> 409 ok")

        # Cancelled load not in browse list
        r = await client.get("/api/loads", headers=other_h)
        assert load_id not in [l["id"] for l in r.json()]
        print("cancelled load excluded from browse")

        # Bad payload → 422
        r = await client.post("/api/loads", json={"title": "x"}, headers=shipper_h)
        assert r.status_code == 422
        print("missing fields -> 422 ok")

        # Window end before start → 422
        bad = _load_payload() | {
            "pickup_window_end": (datetime.now(UTC) - timedelta(days=10)).isoformat()
        }
        r = await client.post("/api/loads", json=bad, headers=shipper_h)
        assert r.status_code == 422, r.text
        print("invalid window -> 422 ok")

    print("\nAll Phase 2 checks passed.")


if __name__ == "__main__":
    asyncio.run(main())
