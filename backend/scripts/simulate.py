"""Shipper/hauler simulation harness — drive the booking + Stripe payment flow.

Runs many concurrent shippers posting loads and haulers claiming them through the
real HTTP API, covering the happy path plus refunds, accept races, missing
card/Connect, declines, and disputes, then asserts DB + Payment invariants.

Online (default) — against a running backend + Stripe test mode + Stripe CLI:

    # terminal 1: backend pointed at staging Supabase, STRIPE_SECRET_KEY=sk_test_...
    uv run python -m app.main
    # terminal 2: forward webhooks (copy whsec_ into STRIPE_WEBHOOK_SECRET, restart backend)
    stripe listen --forward-to localhost:8000/api/webhooks/stripe
    # terminal 3:
    uv run python -m scripts.simulate --shippers 10 --haulers 6 --loads 5
    uv run python -m scripts.simulate --cleanup <run_id>

Offline — no Stripe, no server, ephemeral SQLite (exercises booking + bookkeeping):

    uv run python -m scripts.simulate --offline

Preflight — one happy load end to end, then clean up (sanity-check setup):

    uv run python -m scripts.simulate --preflight
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
logger = logging.getLogger("simulate")


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Shipper/hauler Stripe+DB simulation")
    p.add_argument("--base-url", default="http://localhost:8000")
    p.add_argument("--offline", action="store_true",
                   help="In-process ASGI app + SQLite, no Stripe (bookkeeping mode)")
    p.add_argument("--bookkeeping", action="store_true",
                   help="Online but force Stripe off even if keys are present")
    p.add_argument("--preflight", action="store_true",
                   help="Tiny one-load run to validate setup, then clean up")
    p.add_argument("--cleanup", metavar="RUN_ID",
                   help="Delete all rows created by a previous run and exit")
    p.add_argument("--shippers", type=int, default=6)
    p.add_argument("--haulers", type=int, default=4)
    p.add_argument("--loads", type=int, default=3, help="loads per shipper")
    p.add_argument("--cancel-rate", type=float, default=0.15)
    p.add_argument("--race-rate", type=float, default=0.1)
    p.add_argument("--decline-rate", type=float, default=0.1)
    p.add_argument("--dispute-rate", type=float, default=0.05)
    p.add_argument("--no-card-rate", type=float, default=0.1)
    p.add_argument("--no-connect-rate", type=float, default=0.1)
    p.add_argument("--settle-seconds", type=float, default=6.0)
    p.add_argument("--concurrency", type=int, default=None,
                   help="Max in-flight loads/signups (default: 1 offline, 10 online)")
    return p.parse_args()


def _configure_env(offline: bool) -> None:
    """Must run before importing app modules so settings bind to the right DB."""
    if offline:
        db = Path(__file__).resolve().parent.parent / "tests" / "sim_offline.db"
        os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db}"
        os.environ.setdefault("SECRET_KEY", "sim-secret-key-at-least-32-bytes-long-xx")
        os.environ.pop("STRIPE_SECRET_KEY", None)
        os.environ.pop("STRIPE_WEBHOOK_SECRET", None)
        os.environ.pop("GOOGLE_MAPS_API_KEY", None)


def _build_config(args: argparse.Namespace, run_id: str, stripe_enabled: bool):
    from scripts.sim.config import SimConfig
    cfg = SimConfig(
        run_id=run_id, base_url=args.base_url, offline=args.offline,
        stripe_enabled=stripe_enabled,
        shippers=args.shippers, haulers=args.haulers, loads_per_shipper=args.loads,
        cancel_rate=args.cancel_rate, race_rate=args.race_rate,
        decline_rate=args.decline_rate, dispute_rate=args.dispute_rate,
        no_card_rate=args.no_card_rate, no_connect_rate=args.no_connect_rate,
        settle_seconds=args.settle_seconds,
        max_concurrency=args.concurrency if args.concurrency
        else (1 if args.offline else 10),
    )
    if args.preflight:
        cfg.shippers, cfg.haulers, cfg.loads_per_shipper = 1, 1, 1
        cfg.cancel_rate = cfg.race_rate = cfg.decline_rate = 0.0
        cfg.dispute_rate = cfg.no_card_rate = cfg.no_connect_rate = 0.0
    return cfg


async def _run(args: argparse.Namespace) -> int:
    from scripts.sim import cleanup as cleanup_mod
    from scripts.sim import report
    from scripts.sim.config import new_run_id
    from scripts.sim.runner import run_simulation

    if args.cleanup:
        deleted = await cleanup_mod.cleanup(args.cleanup)
        logger.info("cleanup complete: %s", deleted)
        return 0

    from app.core.config import settings
    stripe_enabled = bool(settings.stripe_secret_key) and not args.offline and not args.bookkeeping
    cfg = _build_config(args, new_run_id(), stripe_enabled)

    client = await _make_client(args.offline, cfg.base_url)
    try:
        results, checks = await run_simulation(client, cfg)
    finally:
        await client.aclose()

    all_ok = report.print_report(cfg, results, checks)
    report.write_json(Path(__file__).resolve().parent.parent / "logs" / f"sim-{cfg.run_id}.json",
                      cfg, results, checks)

    if args.preflight:
        logger.info("preflight cleanup for run %s", cfg.run_id)
        await cleanup_mod.cleanup(cfg.run_id)

    return 0 if all_ok else 1


async def _make_client(offline: bool, base_url: str):
    import httpx
    if offline:
        from app.databases import Base, engine
        import app.models  # noqa: F401  register mappers
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        from app.main import app
        return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")
    return httpx.AsyncClient(base_url=base_url, timeout=30.0)


def main() -> None:
    args = _parse_args()
    _configure_env(args.offline)
    raise SystemExit(asyncio.run(_run(args)))


if __name__ == "__main__":
    main()
