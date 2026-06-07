"""Post-run invariant checks over the HTTP API (+ a direct-DB reconciliation).

Expectations depend on whether Stripe is live: in bookkeeping-only mode payments
still march pending -> transferred but carry no PaymentIntent/transfer ids, and
the Stripe-only scenarios are never planned. Checks adapt via cfg.stripe_enabled.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

import httpx

from . import actors
from .actors import Actor
from .config import SimConfig
from .scenarios import LoadResult

logger = logging.getLogger("sim.assertions")


@dataclass
class Check:
    title: str
    name: str
    ok: bool
    detail: str = ""


def _platform_fee_bps() -> int:
    from app.core.config import settings
    return settings.platform_fee_bps


async def check_results(client: httpx.AsyncClient, cfg: SimConfig,
                        results: list[LoadResult],
                        actors_by_email: dict[str, Actor]) -> list[Check]:
    checks: list[Check] = []
    bps = _platform_fee_bps()
    for r in results:
        try:
            checks.extend(await _check_one(client, cfg, r, actors_by_email, bps))
        except Exception as exc:  # one load's blip shouldn't abort the whole report
            checks.append(Check(r.title, "check_error", False, repr(exc)))
    checks.extend(await _reconcile(cfg, results))
    return checks


async def _check_one(client, cfg, r: LoadResult, actors_by_email, bps) -> list[Check]:
    out: list[Check] = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        out.append(Check(r.title, name, ok, detail))

    if r.error:
        add("posted", False, r.error)
        return out
    if r.load_id is None:
        add("posted", False, "no load id")
        return out

    shipper = actors_by_email[r.shipper_email]

    # Race: exactly one winner.
    if r.scenario == "race":
        ok = r.accept_status is not None and r.accept_status < 400 and r.race_loser_status == 409
        add("race_one_winner", ok, f"winner={r.accept_status} loser={r.race_loser_status}")

    code, pay = await actors.get_payment(client, shipper, r.load_id)
    if code >= 400:
        add("payment_exists", False, f"GET payment -> {code}")
        return out
    add("payment_exists", True)

    # Fee math holds for every payment regardless of scenario.
    amt, fee, payout = pay["amount_cents"], pay["platform_fee_cents"], pay["hauler_payout_cents"]
    add("fee_split_sums", amt == fee + payout, f"{amt} != {fee}+{payout}")
    add("fee_is_bps", fee == amt * bps // 10000, f"fee={fee} expected={amt * bps // 10000}")

    status = pay["status"]
    has_pi = pay["stripe_payment_intent_id"] is not None
    has_transfer = pay["stripe_transfer_id"] is not None

    if r.scenario in ("happy", "race"):
        add("status_transferred", status == "transferred", f"status={status}")
        if cfg.stripe_enabled:
            add("transfer_id_set", has_transfer, "no stripe_transfer_id")
    elif r.scenario == "cancel":
        add("status_refunded", status == "refunded", f"status={status}")
        add("refunded_at_set", pay["refunded_at"] is not None)
    elif r.scenario in ("no_card", "no_connect"):
        add("status_pending", status == "pending", f"status={status}")
        add("no_payment_intent", not has_pi, f"pi={pay['stripe_payment_intent_id']}")
    elif r.scenario == "decline":
        add("status_failed", status == "failed", f"status={status}")
        # error_message is not exposed by the payment API; read it from the DB.
        db_pay = await _db_payment(r.load_id)
        add("error_message_set", bool(db_pay and db_pay.error_message),
            (db_pay.error_message or "")[:80] if db_pay else "no row")
    elif r.scenario == "dispute":
        add("status_transferred", status == "transferred", f"status={status}")
        ok, detail = await _poll_for_dispute(r.load_id, cfg.settle_seconds)
        add("dispute_flagged", ok, detail)

    # Event-chain shape.
    events = await actors.get_events(client, shipper, r.load_id)
    types = [e["event_type"] for e in events]
    add("events_ordered", _events_ok(r.scenario, types, r.delivered), f"events={types}")

    return out


def _events_ok(scenario: str, types: list[str], delivered: bool) -> bool:
    if scenario == "cancel":
        return types == ["accepted", "cancelled"]
    if scenario in ("no_card", "no_connect", "decline"):
        return types == ["accepted"]
    # happy / race / dispute
    if delivered:
        return types == ["accepted", "picked_up", "in_transit", "delivered"]
    return types[:1] == ["accepted"]


async def _db_payment(load_id: str):
    """Latest Payment row for a load, read straight from the DB."""
    from sqlalchemy import select

    from app.databases import AsyncSessionLocal
    from app.models.payment import Payment

    async with AsyncSessionLocal() as db:
        return await db.scalar(
            select(Payment).where(Payment.load_id == load_id)
            .order_by(Payment.created_at.desc()).limit(1)
        )


async def _poll_for_dispute(load_id, settle_seconds) -> tuple[bool, str]:
    """Disputes arrive asynchronously via webhook; poll the DB until flagged."""
    deadline = max(settle_seconds, 30.0)
    waited = 0.0
    while waited < deadline:
        pay = await _db_payment(load_id)
        msg = (pay.error_message if pay else None) or ""
        if "Dispute" in msg:
            return True, msg
        await asyncio.sleep(2.0)
        waited += 2.0
    return False, "no dispute flag within window"


async def _reconcile(cfg: SimConfig, results: list[LoadResult]) -> list[Check]:
    """Direct-DB safety net: at most one payment row per load this run."""
    from sqlalchemy import func, select

    from app.databases import AsyncSessionLocal
    from app.models.payment import Payment

    load_ids = [r.load_id for r in results if r.load_id]
    if not load_ids:
        return []
    async with AsyncSessionLocal() as db:
        rows = (await db.execute(
            select(Payment.load_id, func.count())
            .where(Payment.load_id.in_(load_ids))
            .group_by(Payment.load_id)
        )).all()
    over = [lid for lid, n in rows if n > 1]
    return [Check("(reconcile)", "one_payment_per_load", not over,
                  f"loads with >1 payment: {over}" if over else "")]
