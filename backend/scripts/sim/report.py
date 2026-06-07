"""Console summary + JSON report for a simulation run."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path

from .assertions import Check
from .config import SimConfig
from .scenarios import LoadResult


def print_report(cfg: SimConfig, results: list[LoadResult], checks: list[Check]) -> bool:
    by_scenario: dict[str, list[Check]] = defaultdict(list)
    scenario_of_title = {r.title: r.scenario for r in results}
    for c in checks:
        by_scenario[scenario_of_title.get(c.title, "(global)")].append(c)

    print(f"\n=== Simulation report  run={cfg.run_id}  "
          f"mode={'offline' if cfg.offline else 'online'}  "
          f"stripe={'on' if cfg.stripe_enabled else 'off'} ===")
    print(f"loads={len(results)}  checks={len(checks)}")

    all_ok = True
    for scenario in sorted(by_scenario):
        group = by_scenario[scenario]
        passed = sum(1 for c in group if c.ok)
        ok = passed == len(group)
        all_ok = all_ok and ok
        flag = "PASS" if ok else "FAIL"
        print(f"\n  [{flag}] {scenario}: {passed}/{len(group)} checks")
        for c in group:
            if not c.ok:
                print(f"      ✗ {c.title} :: {c.name} — {c.detail}")

    print(f"\n=== {'ALL PASS' if all_ok else 'FAILURES PRESENT'} ===\n")
    return all_ok


def write_json(path: Path, cfg: SimConfig, results: list[LoadResult],
               checks: list[Check]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_id": cfg.run_id,
        "config": {k: v for k, v in asdict(cfg).items()},
        "results": [asdict(r) for r in results],
        "checks": [asdict(c) for c in checks],
        "all_ok": all(c.ok for c in checks),
    }
    path.write_text(json.dumps(payload, indent=2, default=str))
