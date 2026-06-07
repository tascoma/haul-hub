"""Per-load scenario executors.

Each runner posts one load and drives it to a terminal state, recording what
happened in a LoadResult that assertions.py later validates. Runners use the HTTP
helpers in actors.py so the booking + payment services run for real.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field

import httpx

from . import actors
from .actors import Actor
from .config import SimConfig

logger = logging.getLogger("sim.scenarios")


@dataclass
class LoadPlan:
    scenario: str
    title: str
    pickup: dict
    dropoff: dict


@dataclass
class LoadResult:
    scenario: str
    title: str
    load_id: str | None = None
    shipper_email: str = ""
    hauler_email: str | None = None
    accept_status: int | None = None
    race_loser_status: int | None = None
    delivered: bool = False
    cancelled: bool = False
    error: str | None = None
    notes: list[str] = field(default_factory=list)


async def _run_lifecycle(client: httpx.AsyncClient, hauler: Actor, load_id: str,
                         result: LoadResult) -> None:
    """accept already done by caller; carry through pickup -> in_transit -> deliver."""
    for action, fn in (("pickup", actors.pickup), ("in-transit", actors.in_transit),
                       ("deliver", actors.deliver)):
        code, _ = await fn(client, hauler, load_id)
        if code >= 400:
            result.notes.append(f"{action} failed ({code})")
            return
    result.delivered = True


async def run_load(client: httpx.AsyncClient, cfg: SimConfig, plan: LoadPlan,
                   shipper: Actor, haulers: list[Actor]) -> LoadResult:
    result = LoadResult(scenario=plan.scenario, title=plan.title, shipper_email=shipper.email)
    try:
        result.load_id = await actors.post_load(client, shipper, plan.title, plan.pickup, plan.dropoff)
    except (actors.ApiError, httpx.HTTPError) as exc:
        result.error = f"post_load: {exc}"
        return result

    hauler = haulers[0]
    result.hauler_email = hauler.email

    if plan.scenario == "race":
        return await _run_race(client, plan, result, haulers)

    code, _ = await actors.accept(client, hauler, result.load_id)
    result.accept_status = code
    if code >= 400:
        result.notes.append(f"accept rejected ({code})")
        return result

    if plan.scenario == "cancel":
        ccode, _ = await actors.cancel(client, shipper, result.load_id)
        result.cancelled = ccode < 400
        if ccode >= 400:
            result.notes.append(f"cancel failed ({ccode})")
        return result

    if plan.scenario in ("decline", "no_card", "no_connect"):
        # Stop at accept: authorize already decided the payment's fate. Driving the
        # load to delivery would let the bookkeeping path overwrite it (e.g. a
        # missing-PaymentIntent capture marks the row 'transferred'), masking the
        # very behaviour these scenarios assert (no PaymentIntent / failed auth).
        return result

    # happy / dispute run the full delivery lifecycle to exercise capture+transfer.
    await _run_lifecycle(client, hauler, result.load_id, result)
    return result


async def _run_race(client: httpx.AsyncClient, plan: LoadPlan, result: LoadResult,
                    haulers: list[Actor]) -> LoadResult:
    """Two haulers accept the same load at once; exactly one must win."""
    h1, h2 = haulers[0], haulers[1]
    (c1, _), (c2, _) = await asyncio.gather(
        actors.accept(client, h1, result.load_id),
        actors.accept(client, h2, result.load_id),
    )
    codes = sorted([c1, c2])
    winner = h1 if c1 < c2 else h2
    result.hauler_email = winner.email
    result.accept_status = codes[0]
    result.race_loser_status = codes[1]
    if codes[0] >= 400 or codes[1] < 400:
        result.notes.append(f"race not exactly-one-winner: {codes}")
        return result
    await _run_lifecycle(client, winner, result.load_id, result)
    return result
