"""Shipper/hauler simulation harness for exercising the Stripe + DB payment flow.

See scripts/simulate.py for the CLI entrypoint and scripts/sim/README is in the
plan file. Modules:

- config:        run identity, counts, rates, markers, fixed test data
- stripe_setup:  test-mode card + enabled Connect account creation (online only)
- actors:        HTTP helpers for signup / posting / the booking lifecycle
- scenarios:     per-load scenario runners (happy, cancel, race, decline, ...)
- assertions:    post-run invariant checks over the HTTP API + DB
- report:        console summary table + JSON report
- cleanup:       delete sim-tagged rows by run id
"""
