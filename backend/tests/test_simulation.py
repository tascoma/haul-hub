"""Offline self-test for the simulation harness.

Runs a tiny bookkeeping-mode simulation against the in-process app + SQLite (the
conftest setup pops Stripe keys, so payments march pending -> transferred with no
Stripe calls) and asserts the harness's own invariant checks all pass. This keeps
the harness logic CI-testable without Stripe or Supabase.
"""

from scripts.sim.config import SimConfig, new_run_id
from scripts.sim.runner import run_simulation


async def test_offline_simulation_all_checks_pass(client):
    # Race is intentionally excluded: it probes whether concurrent double-accept
    # is rejected, which the app does not guarantee under a single-process event
    # loop — a finding worth surfacing in a real run, but not deterministic here.
    cfg = SimConfig(
        run_id=new_run_id(),
        offline=True,
        stripe_enabled=False,
        shippers=2,
        haulers=2,
        loads_per_shipper=3,
        cancel_rate=0.5,    # ~3 cancels, rest happy
        race_rate=0.0,
        decline_rate=0.0, dispute_rate=0.0, no_card_rate=0.0, no_connect_rate=0.0,
        settle_seconds=0.0,
        max_concurrency=1,  # SQLite: avoid writer-lock contention
    )

    results, checks = await run_simulation(client, cfg)

    assert results, "no loads were simulated"
    scenarios = {r.scenario for r in results}
    assert {"happy", "cancel"} <= scenarios, f"expected happy+cancel, got {scenarios}"

    failures = [(c.title, c.name, c.detail) for c in checks if not c.ok]
    assert not failures, f"harness invariant checks failed: {failures}"

    # Bookkeeping mode: terminal happy loads transfer with no Stripe ids.
    delivered = [r for r in results if r.scenario == "happy" and r.delivered]
    assert delivered, "expected at least one delivered load"
