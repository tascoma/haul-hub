"""Static configuration, run identity, and marker helpers for the simulation.

Every row the harness writes is tagged with the run id so a run is fully
identifiable and removable from a shared database (see cleanup.py). The marker
lives in user emails and load titles.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field

# ── Markers ──────────────────────────────────────────────────────────────────
# Bumping this prefix invalidates --cleanup for older runs, so keep it stable.
TITLE_PREFIX = "[SIM"
PASSWORD = "simulation-pw-12345"


def new_run_id() -> str:
    """Short, URL/email-safe id unique to one simulation run."""
    return secrets.token_hex(4)


# Reserved TLDs (.test/.example/.invalid) are rejected by email-validator, so use
# a normal domain and carry the run-id marker in the local part instead.
SIM_EMAIL_DOMAIN = "haulhubsim.com"


def shipper_email(run_id: str, n: int) -> str:
    return f"sim+{run_id}+shipper{n}@{SIM_EMAIL_DOMAIN}"


def hauler_email(run_id: str, n: int) -> str:
    return f"sim+{run_id}+hauler{n}@{SIM_EMAIL_DOMAIN}"


def email_marker(run_id: str) -> str:
    """SQL LIKE pattern matching every user this run created."""
    return f"sim+{run_id}+%@{SIM_EMAIL_DOMAIN}"


def load_title(run_id: str, scenario: str, n: int) -> str:
    return f"{TITLE_PREFIX} {run_id}] {scenario} #{n}"


def title_marker(run_id: str) -> str:
    return f"{TITLE_PREFIX} {run_id}]%"


# ── Stripe test PaymentMethods (test mode only) ──────────────────────────────
# pm_card_visa / pm_card_chargeDeclined are stable Stripe test PaymentMethod
# ids. The dispute method is built from a card token at runtime in stripe_setup.
PM_VISA = "pm_card_visa"
PM_DECLINE = "pm_card_chargeDeclined"
DISPUTE_CARD_TOKEN = "tok_createDispute"  # charge succeeds then auto-disputes

# ── Fixed, geocodable addresses (kept small + deterministic) ─────────────────
# Real US addresses so online runs geocode cleanly; offline runs ignore lat/lng.
ADDRESSES: list[dict[str, str]] = [
    {"address": "1600 Amphitheatre Parkway", "city": "Mountain View", "state": "CA", "zip": "94043"},
    {"address": "1 Apple Park Way", "city": "Cupertino", "state": "CA", "zip": "95014"},
    {"address": "410 Terry Ave N", "city": "Seattle", "state": "WA", "zip": "98109"},
    {"address": "1355 Market St", "city": "San Francisco", "state": "CA", "zip": "94103"},
    {"address": "350 5th Ave", "city": "New York", "state": "NY", "zip": "10118"},
    {"address": "233 S Wacker Dr", "city": "Chicago", "state": "IL", "zip": "60606"},
]

# Scenarios that only have distinct, assertable behaviour when Stripe is live.
STRIPE_ONLY_SCENARIOS = {"no_card", "no_connect", "decline", "dispute"}
ALL_SCENARIOS = {"happy", "cancel", "race", *STRIPE_ONLY_SCENARIOS}


@dataclass
class SimConfig:
    run_id: str
    base_url: str = "http://localhost:8000"
    offline: bool = False
    # When False the harness expects bookkeeping-only behaviour (no PI ids, no
    # transfers) and downgrades Stripe-only scenarios to happy.
    stripe_enabled: bool = True

    shippers: int = 6
    haulers: int = 4
    loads_per_shipper: int = 3

    cancel_rate: float = 0.15
    race_rate: float = 0.1
    decline_rate: float = 0.1
    dispute_rate: float = 0.05
    no_card_rate: float = 0.1
    no_connect_rate: float = 0.1

    # Seconds to let Stripe-CLI-forwarded webhooks settle before asserting.
    settle_seconds: float = 6.0
    # Concurrent in-flight loads/signups. Keep at 1 for SQLite (offline) to avoid
    # writer-lock contention; raise it for Postgres/staging.
    max_concurrency: int = 10

    # Populated by stripe_setup / cleanup as the run proceeds.
    connect_account_ids: list[str] = field(default_factory=list)

    @property
    def total_loads(self) -> int:
        return self.shippers * self.loads_per_shipper
