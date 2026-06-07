"""HTTP + DB helpers that drive the public API the way real shippers/haulers do.

Each call goes through the real FastAPI surface (httpx client) so the harness
tests routing, auth, services, and persistence end to end. The one exception is
set_connect_account, which writes the hauler's Stripe Connect id straight to the
DB — there is no API to inject an already-onboarded account (see stripe_setup).
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

import httpx

from . import config

logger = logging.getLogger("sim.actors")

# Transient connection blips against a local server / pooler (DNS hiccups, dropped
# reads under a concurrency burst) — retried rather than crashing the run.
_TRANSIENT = (
    httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadError, httpx.ReadTimeout,
    httpx.WriteError, httpx.RemoteProtocolError, httpx.PoolTimeout,
)
_RETRIES = 4


async def _send(client: httpx.AsyncClient, method: str, url: str, *,
                idempotent: bool = False, **kwargs) -> httpx.Response:
    """Issue a request, retrying transient transport errors (always) and 5xx
    (only for idempotent calls, so non-idempotent POSTs aren't double-applied).
    """
    last_exc: Exception | None = None
    for attempt in range(_RETRIES):
        try:
            resp = await client.request(method, url, **kwargs)
        except _TRANSIENT as exc:
            last_exc = exc
            await asyncio.sleep(0.4 * (attempt + 1))
            continue
        if idempotent and resp.status_code >= 500 and attempt < _RETRIES - 1:
            await asyncio.sleep(0.4 * (attempt + 1))
            continue
        return resp
    raise last_exc  # type: ignore[misc]


@dataclass
class Actor:
    user_id: str
    email: str
    headers: dict[str, str]
    # hauler-only
    connect_account_id: str | None = None
    has_card: bool = False
    posted_load_ids: list[str] = field(default_factory=list)


class ApiError(RuntimeError):
    def __init__(self, method: str, path: str, resp: httpx.Response) -> None:
        super().__init__(f"{method} {path} -> {resp.status_code}: {resp.text[:300]}")
        self.status_code = resp.status_code


def _safe_json(resp: httpx.Response) -> dict:
    """Parse a JSON body, tolerating empty or non-JSON (e.g. a 500 HTML page)."""
    if not resp.content:
        return {}
    try:
        return resp.json()
    except ValueError:
        return {"_non_json_body": resp.text[:200]}


async def _ok(resp: httpx.Response, method: str, path: str) -> dict:
    if resp.status_code >= 400:
        raise ApiError(method, path, resp)
    return _safe_json(resp)


# ── Account setup ────────────────────────────────────────────────────────────

async def signup(client: httpx.AsyncClient, email: str, roles: list[str]) -> Actor:
    await _ok(
        await _send(
            client, "POST", "/api/auth/signup", idempotent=True,
            json={"email": email, "password": config.PASSWORD,
                  "full_name": email.split("@")[0], "roles": roles},
        ),
        "POST", "/api/auth/signup",
    )
    # Log in to obtain a token, then read identity.
    token_body = await _ok(
        await _send(client, "POST", "/api/auth/login", idempotent=True,
                    json={"email": email, "password": config.PASSWORD}),
        "POST", "/api/auth/login",
    )
    headers = {"Authorization": f"Bearer {token_body['access_token']}"}
    me = await _ok(
        await _send(client, "GET", "/api/me", idempotent=True, headers=headers),
        "GET", "/api/me",
    )
    # A non-empty full_name + phone makes the profile "complete" for onboarding checks.
    await _ok(
        await _send(client, "PATCH", "/api/me", idempotent=True,
                    headers=headers, json={"phone": "555-0100"}),
        "PATCH", "/api/me",
    )
    return Actor(user_id=me["id"], email=email, headers=headers)


async def save_card(client: httpx.AsyncClient, actor: Actor, payment_method_id: str) -> None:
    await _ok(
        await _send(
            client, "POST", "/api/me/payment-method", idempotent=True,
            headers=actor.headers, json={"payment_method_id": payment_method_id},
        ),
        "POST", "/api/me/payment-method",
    )
    actor.has_card = True


async def connect_onboarding_url(client: httpx.AsyncClient, actor: Actor) -> str:
    """Exercise the real onboarding endpoint (returns a hosted-onboarding URL)."""
    body = await _ok(
        await _send(client, "POST", "/api/me/connect-onboarding", headers=actor.headers),
        "POST", "/api/me/connect-onboarding",
    )
    return body["url"]


async def set_connect_account(actor: Actor, account_id: str) -> None:
    """Write an already-enabled Connect account id straight onto the profile.

    Imported lazily so offline runs (no Stripe) never need a DB engine here.
    """
    from sqlalchemy import update

    from app.databases import AsyncSessionLocal
    from app.models.user import UserProfile

    async with AsyncSessionLocal() as db:
        await db.execute(
            update(UserProfile)
            .where(UserProfile.user_id == actor.user_id)
            .values(stripe_connect_account_id=account_id,
                    stripe_charges_enabled=True, stripe_payouts_enabled=True,
                    stripe_details_submitted=True)
        )
        await db.commit()
    actor.connect_account_id = account_id


# ── Loads ────────────────────────────────────────────────────────────────────

def _load_payload(title: str, pickup: dict, dropoff: dict) -> dict:
    now = datetime.now(UTC)
    return {
        "title": title,
        "description": "Simulated haul",
        "weight_lbs": 500,
        "pickup_address": pickup["address"], "pickup_city": pickup["city"],
        "pickup_state": pickup["state"], "pickup_zip": pickup["zip"],
        "pickup_window_start": (now + timedelta(days=1)).isoformat(),
        "pickup_window_end": (now + timedelta(days=1, hours=4)).isoformat(),
        "dropoff_address": dropoff["address"], "dropoff_city": dropoff["city"],
        "dropoff_state": dropoff["state"], "dropoff_zip": dropoff["zip"],
        "dropoff_by": (now + timedelta(days=2)).isoformat(),
        "estimated_distance_miles": 25.0,
        "urgency": "standard",
    }


async def post_load(client: httpx.AsyncClient, shipper: Actor, title: str,
                    pickup: dict, dropoff: dict) -> str:
    body = await _ok(
        await _send(
            client, "POST", "/api/loads", headers=shipper.headers,
            json=_load_payload(title, pickup, dropoff),
        ),
        "POST", "/api/loads",
    )
    shipper.posted_load_ids.append(body["id"])
    return body["id"]


# ── Booking lifecycle (return (status_code, json) so callers can assert races) ─

async def _post_transition(client: httpx.AsyncClient, actor: Actor, load_id: str,
                           action: str) -> tuple[int, dict]:
    resp = await _send(client, "POST", f"/api/loads/{load_id}/{action}", headers=actor.headers)
    return resp.status_code, _safe_json(resp)


async def accept(client, actor, load_id): return await _post_transition(client, actor, load_id, "accept")
async def pickup(client, actor, load_id): return await _post_transition(client, actor, load_id, "pickup")
async def in_transit(client, actor, load_id): return await _post_transition(client, actor, load_id, "in-transit")
async def deliver(client, actor, load_id): return await _post_transition(client, actor, load_id, "deliver")


async def cancel(client: httpx.AsyncClient, actor: Actor, load_id: str,
                 reason: str = "sim cancel") -> tuple[int, dict]:
    resp = await _send(
        client, "POST", f"/api/loads/{load_id}/cancel",
        headers=actor.headers, json={"reason": reason},
    )
    return resp.status_code, _safe_json(resp)


async def get_payment(client: httpx.AsyncClient, actor: Actor, load_id: str) -> tuple[int, dict]:
    resp = await _send(client, "GET", f"/api/loads/{load_id}/payment",
                       idempotent=True, headers=actor.headers)
    return resp.status_code, _safe_json(resp)


async def get_events(client: httpx.AsyncClient, actor: Actor, load_id: str) -> list[dict]:
    resp = await _send(client, "GET", f"/api/loads/{load_id}/events",
                       idempotent=True, headers=actor.headers)
    return resp.json() if resp.status_code < 400 and resp.content else []
