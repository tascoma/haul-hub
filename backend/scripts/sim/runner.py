"""Mode-agnostic orchestration: provision actors, plan loads, run, assert.

Both the CLI (scripts/simulate.py) and the offline pytest call run_simulation with
a ready httpx client, so the same code path is exercised online and offline.
"""

from __future__ import annotations

import asyncio
import logging

import httpx

from . import actors, assertions, config, scenarios, stripe_setup
from .actors import Actor
from .config import SimConfig
from .scenarios import LoadPlan, LoadResult

logger = logging.getLogger("sim.runner")


async def _bounded_gather(coros: list, limit: int) -> list:
    """Run coroutines with at most `limit` in flight (SQLite-safe at limit=1)."""
    sem = asyncio.Semaphore(max(limit, 1))

    async def _wrap(coro):
        async with sem:
            return await coro

    return list(await asyncio.gather(*[_wrap(c) for c in coros]))


# Shipper card bucket required by each scenario.
_SHIPPER_KIND = {
    "happy": "visa", "cancel": "visa", "race": "visa", "no_connect": "visa",
    "no_card": "none", "decline": "decline", "dispute": "dispute",
}


# ── Planning ─────────────────────────────────────────────────────────────────

def build_plans(cfg: SimConfig) -> list[LoadPlan]:
    n = cfg.total_loads
    counts: dict[str, int] = {
        "cancel": round(n * cfg.cancel_rate),
        "race": round(n * cfg.race_rate),
    }
    if cfg.stripe_enabled:
        counts["no_card"] = round(n * cfg.no_card_rate)
        counts["no_connect"] = round(n * cfg.no_connect_rate)
        counts["decline"] = round(n * cfg.decline_rate)
        counts["dispute"] = round(n * cfg.dispute_rate)
    counts["happy"] = max(n - sum(counts.values()), 0)

    plans: list[LoadPlan] = []
    i = 0
    for scenario, c in counts.items():
        for _ in range(c):
            pu = config.ADDRESSES[i % len(config.ADDRESSES)]
            do = config.ADDRESSES[(i + 1) % len(config.ADDRESSES)]
            plans.append(LoadPlan(scenario, config.load_title(cfg.run_id, scenario, i), pu, do))
            i += 1
    return plans


# ── Provisioning ─────────────────────────────────────────────────────────────

class Pools:
    def __init__(self) -> None:
        self.shippers: dict[str, list[Actor]] = {"visa": [], "none": [], "decline": [], "dispute": []}
        self.haulers_connect: list[Actor] = []
        self.haulers_noconnect: list[Actor] = []
        self.by_email: dict[str, Actor] = {}

    def register(self, actor: Actor) -> None:
        self.by_email[actor.email] = actor


async def provision(client: httpx.AsyncClient, cfg: SimConfig,
                    scenarios_present: set[str]) -> Pools:
    pools = Pools()
    counter = {"n": 0}

    async def make_shipper(kind: str) -> None:
        n = counter["n"]; counter["n"] += 1
        actor = await actors.signup(client, config.shipper_email(cfg.run_id, n), ["customer"])
        if cfg.stripe_enabled and kind != "none":
            pm_kind = {"visa": "visa", "decline": "decline", "dispute": "dispute"}[kind]
            await actors.save_card(client, actor, await stripe_setup.payment_method_for(pm_kind))
        pools.shippers[kind].append(actor)
        pools.register(actor)

    async def make_hauler(connected: bool, idx: int) -> None:
        actor = await actors.signup(client, config.hauler_email(cfg.run_id, idx), ["hauler"])
        if connected and cfg.stripe_enabled:
            # Exercise the real onboarding endpoint (creates an Express account +
            # returns a hosted URL), then overwrite with an instantly-enabled test
            # account so the transfer leg actually completes (see stripe_setup).
            await actors.connect_onboarding_url(client, actor)
            acct = await stripe_setup.create_enabled_connect_account(actor.email)
            cfg.connect_account_ids.append(acct)
            await actors.set_connect_account(actor, acct)
        (pools.haulers_connect if connected else pools.haulers_noconnect).append(actor)
        pools.register(actor)

    # How many of each shipper bucket do we need?
    shipper_jobs: list[str] = ["visa"] * max(cfg.shippers, 1)
    for kind in ("none", "decline", "dispute"):
        scen = {"none": "no_card", "decline": "decline", "dispute": "dispute"}[kind]
        if scen in scenarios_present:
            shipper_jobs.append(kind)

    # Haulers: connect pool (>=2 if a race is planned) + one no-connect if needed.
    n_connect = max(cfg.haulers, 2 if "race" in scenarios_present else 1)
    hidx = {"n": 0}
    hauler_jobs: list[bool] = [True] * n_connect
    if "no_connect" in scenarios_present:
        hauler_jobs.append(False)

    await _bounded_gather(
        [make_shipper(k) for k in shipper_jobs]
        + [make_hauler(c, i) for i, c in enumerate(hauler_jobs)],
        cfg.max_concurrency,
    )
    return pools


# ── Run ──────────────────────────────────────────────────────────────────────

def _assign_haulers(pools: Pools, scenario: str, rr: dict[str, int]) -> list[Actor]:
    if scenario == "no_connect":
        return [pools.haulers_noconnect[0]]
    pool = pools.haulers_connect
    i = rr["h"]; rr["h"] += 1
    if scenario == "race":
        return [pool[i % len(pool)], pool[(i + 1) % len(pool)]]
    return [pool[i % len(pool)]]


def _assign_shipper(pools: Pools, scenario: str, rr: dict[str, int]) -> Actor:
    kind = _SHIPPER_KIND[scenario]
    pool = pools.shippers[kind]
    key = f"s_{kind}"
    i = rr.get(key, 0); rr[key] = i + 1
    return pool[i % len(pool)]


async def run_simulation(client: httpx.AsyncClient, cfg: SimConfig
                         ) -> tuple[list[LoadResult], list[assertions.Check]]:
    if cfg.stripe_enabled:
        from app.core.config import settings
        if not settings.stripe_secret_key:
            raise SystemExit("stripe_enabled but STRIPE_SECRET_KEY is unset")
        stripe_setup.init(settings.stripe_secret_key)

    plans = build_plans(cfg)
    scenarios_present = {p.scenario for p in plans}
    logger.info("run=%s plans=%s", cfg.run_id, {s: sum(p.scenario == s for p in plans) for s in scenarios_present})

    pools = await provision(client, cfg, scenarios_present)

    rr: dict[str, int] = {"h": 0}
    # Assign actors up front (cheap, deterministic) so the concurrent phase only
    # does I/O and the round-robin counters aren't racing.
    assigned = [(p, _assign_shipper(pools, p.scenario, rr), _assign_haulers(pools, p.scenario, rr))
                for p in plans]
    results = await _bounded_gather(
        [scenarios.run_load(client, cfg, p, s, h) for p, s, h in assigned],
        cfg.max_concurrency,
    )

    if cfg.stripe_enabled and not cfg.offline and cfg.settle_seconds:
        logger.info("settling %.1fs for webhooks", cfg.settle_seconds)
        await asyncio.sleep(cfg.settle_seconds)

    checks = await assertions.check_results(client, cfg, list(results), pools.by_email)
    return list(results), checks
