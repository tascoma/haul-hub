"""Production-hardening coverage for the Stripe payment flow.

Unlike test_payments.py (bookkeeping-only, skipped when a real key is present),
these tests fake the `stripe` module or call webhook handlers directly, so they
run regardless of whether STRIPE_SECRET_KEY is set.
"""

import types
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.databases import AsyncSessionLocal
from app.models.load import Load
from app.models.payment import Payment, PaymentStatus
from app.models.user import User
from app.services import payments


def _load_payload() -> dict:
    now = datetime.now(UTC)
    return {
        "title": "Hardening payment load",
        "weight_lbs": 2000,
        "pickup_address": "1 A St",
        "pickup_city": "Austin",
        "pickup_state": "TX",
        "pickup_zip": "78701",
        "pickup_window_start": (now + timedelta(days=1)).isoformat(),
        "pickup_window_end": (now + timedelta(days=1, hours=4)).isoformat(),
        "dropoff_address": "2 B St",
        "dropoff_city": "Houston",
        "dropoff_state": "TX",
        "dropoff_zip": "77001",
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


async def _enable_hauler(client: AsyncClient, headers: dict) -> None:
    r = await client.post(
        "/api/me/enable-hauler", json={"service_radius_miles": 25}, headers=headers
    )
    assert r.status_code == 201, r.text
    r = await client.post(
        "/api/me/vehicles",
        json={"vehicle_type": "pickup", "max_payload_lbs": 5000, "is_default": True},
        headers=headers,
    )
    assert r.status_code == 201, r.text


SHIPPER_EMAIL = "shipper_hard@example.com"
HAULER_EMAIL = "hauler_hard@example.com"


@pytest.fixture
async def actors(client: AsyncClient) -> dict[str, dict]:
    shipper = {"Authorization": f"Bearer {await _signup(client, SHIPPER_EMAIL)}"}
    hauler = {"Authorization": f"Bearer {await _signup(client, HAULER_EMAIL)}"}
    await _enable_hauler(client, hauler)
    return {"shipper": shipper, "hauler": hauler}


async def _payment_for(load_id: str) -> Payment | None:
    async with AsyncSessionLocal() as db:
        return await db.scalar(
            select(Payment).where(Payment.load_id == load_id).order_by(Payment.created_at.desc())
        )


async def _set_profile(email: str, **fields) -> None:
    async with AsyncSessionLocal() as db:
        user = await db.scalar(select(User).where(User.email == email))
        for key, value in fields.items():
            setattr(user.profile, key, value)
        await db.commit()


async def _seed_authorized_payment(load_id: str, pi_id: str = "pi_existing") -> str:
    async with AsyncSessionLocal() as db:
        payment = await db.scalar(select(Payment).where(Payment.load_id == load_id))
        payment.status = PaymentStatus.authorized
        payment.stripe_payment_intent_id = pi_id
        await db.commit()
        return payment.id


async def _new_load(client: AsyncClient, actors: dict) -> str:
    load_id = (
        await client.post("/api/loads", json=_load_payload(), headers=actors["shipper"])
    ).json()["id"]
    await client.post(f"/api/loads/{load_id}/accept", headers=actors["hauler"])
    return load_id


def _fake_stripe(recorder: dict, *, transfer_id: str = "tr_test", charge_id: str = "ch_test"):
    """A stand-in for the `stripe` module that records call kwargs."""

    class _Err(Exception):
        pass

    class PaymentIntent:
        @staticmethod
        def create(**kwargs):
            recorder["create"] = kwargs
            return types.SimpleNamespace(id="pi_fake", status="requires_capture")

        @staticmethod
        def capture(pi_id, **kwargs):
            recorder["capture"] = {"pi_id": pi_id, **kwargs}
            return types.SimpleNamespace(latest_charge=charge_id)

        @staticmethod
        def cancel(pi_id, **kwargs):
            recorder["cancel"] = {"pi_id": pi_id, **kwargs}
            return types.SimpleNamespace(id=pi_id, status="canceled")

    class Charge:
        @staticmethod
        def retrieve(cid):
            return types.SimpleNamespace(transfer=transfer_id)

    class Refund:
        @staticmethod
        def create(**kwargs):
            recorder["refund"] = kwargs
            return types.SimpleNamespace(id="re_fake")

    return types.SimpleNamespace(
        PaymentIntent=PaymentIntent, Charge=Charge, Refund=Refund, StripeError=_Err
    )


def _enable_fake_stripe(monkeypatch, recorder: dict) -> None:
    monkeypatch.setattr(payments, "_stripe_enabled", lambda: True)
    monkeypatch.setattr(payments, "stripe", _fake_stripe(recorder))


# ---------------------------------------------------------------------------
# Idempotency keys + state guards on the service
# ---------------------------------------------------------------------------


async def test_authorize_passes_idempotency_key_and_transfer_group(
    client: AsyncClient, actors: dict, monkeypatch
) -> None:
    load_id = (
        await client.post("/api/loads", json=_load_payload(), headers=actors["shipper"])
    ).json()["id"]
    await _set_profile(
        SHIPPER_EMAIL, stripe_customer_id="cus_test", stripe_default_payment_method_id="pm_test"
    )
    await _set_profile(HAULER_EMAIL, stripe_connect_account_id="acct_test")

    recorder: dict = {}
    _enable_fake_stripe(monkeypatch, recorder)
    async with AsyncSessionLocal() as db:
        load = await db.scalar(select(Load).where(Load.id == load_id))
        hauler = await db.scalar(select(User).where(User.email == HAULER_EMAIL))
        payment = await payments.authorize_payment_for_load(db, load, hauler)
        await db.commit()

    assert recorder["create"]["idempotency_key"] == f"authorize:{load_id}"
    assert recorder["create"]["transfer_group"] == f"load_{load_id}"
    assert payment.status == PaymentStatus.authorized
    assert payment.stripe_payment_intent_id == "pi_fake"


async def test_capture_passes_idempotency_key_and_records_transfer(
    client: AsyncClient, actors: dict, monkeypatch
) -> None:
    load_id = await _new_load(client, actors)
    payment_id = await _seed_authorized_payment(load_id)

    recorder: dict = {}
    _enable_fake_stripe(monkeypatch, recorder)
    async with AsyncSessionLocal() as db:
        load = await db.scalar(select(Load).where(Load.id == load_id))
        result = await payments.capture_and_transfer(db, load)
        await db.commit()

    assert recorder["capture"]["idempotency_key"] == f"capture:{payment_id}"
    assert result.status == PaymentStatus.transferred
    assert result.stripe_transfer_id == "tr_test"


async def test_capture_skips_when_already_transferred(
    client: AsyncClient, actors: dict, monkeypatch
) -> None:
    load_id = await _new_load(client, actors)
    async with AsyncSessionLocal() as db:
        payment = await db.scalar(select(Payment).where(Payment.load_id == load_id))
        payment.status = PaymentStatus.transferred
        payment.stripe_payment_intent_id = "pi_existing"
        await db.commit()

    recorder: dict = {}
    _enable_fake_stripe(monkeypatch, recorder)
    async with AsyncSessionLocal() as db:
        load = await db.scalar(select(Load).where(Load.id == load_id))
        await payments.capture_and_transfer(db, load)
        await db.commit()

    assert "capture" not in recorder  # guard prevented a second capture
    payment = await _payment_for(load_id)
    assert payment.status == PaymentStatus.transferred


async def test_cancel_authorized_payment_cancels_intent(
    client: AsyncClient, actors: dict, monkeypatch
) -> None:
    # An authorized (manual-capture) PaymentIntent is uncaptured, so the hold must
    # be released by cancelling the intent — refunding an uncaptured charge errors.
    load_id = await _new_load(client, actors)
    payment_id = await _seed_authorized_payment(load_id)

    recorder: dict = {}
    _enable_fake_stripe(monkeypatch, recorder)
    async with AsyncSessionLocal() as db:
        load = await db.scalar(select(Load).where(Load.id == load_id))
        result = await payments.refund_on_cancel(db, load)
        await db.commit()

    assert recorder["cancel"]["idempotency_key"] == f"cancel:{payment_id}"
    assert "refund" not in recorder  # never refund an uncaptured charge
    assert result.status == PaymentStatus.refunded


async def test_refund_transferred_payment_reverses_transfer(
    client: AsyncClient, actors: dict, monkeypatch
) -> None:
    # Once captured + transferred, cancelling on cancel must refund the charge and
    # claw back the transfer and application fee.
    load_id = await _new_load(client, actors)
    async with AsyncSessionLocal() as db:
        payment = await db.scalar(select(Payment).where(Payment.load_id == load_id))
        payment.status = PaymentStatus.transferred
        payment.stripe_payment_intent_id = "pi_existing"
        await db.commit()
        payment_id = payment.id

    recorder: dict = {}
    _enable_fake_stripe(monkeypatch, recorder)
    async with AsyncSessionLocal() as db:
        load = await db.scalar(select(Load).where(Load.id == load_id))
        result = await payments.refund_on_cancel(db, load)
        await db.commit()

    assert recorder["refund"]["idempotency_key"] == f"refund:{payment_id}"
    assert recorder["refund"]["reverse_transfer"] is True
    assert recorder["refund"]["refund_application_fee"] is True
    assert "cancel" not in recorder
    assert result.status == PaymentStatus.refunded


async def test_refund_skips_when_already_refunded(
    client: AsyncClient, actors: dict, monkeypatch
) -> None:
    load_id = await _new_load(client, actors)
    async with AsyncSessionLocal() as db:
        payment = await db.scalar(select(Payment).where(Payment.load_id == load_id))
        payment.status = PaymentStatus.refunded
        payment.stripe_payment_intent_id = "pi_existing"
        await db.commit()

    recorder: dict = {}
    _enable_fake_stripe(monkeypatch, recorder)
    async with AsyncSessionLocal() as db:
        load = await db.scalar(select(Load).where(Load.id == load_id))
        await payments.refund_on_cancel(db, load)
        await db.commit()

    assert "refund" not in recorder  # guard prevented a second refund


# ---------------------------------------------------------------------------
# Webhook handlers
# ---------------------------------------------------------------------------


async def test_payment_intent_succeeded_does_not_regress_transferred(
    client: AsyncClient, actors: dict
) -> None:
    from app.routes.webhooks import _handle_payment_intent_succeeded

    load_id = await _new_load(client, actors)
    async with AsyncSessionLocal() as db:
        payment = await db.scalar(select(Payment).where(Payment.load_id == load_id))
        payment.status = PaymentStatus.transferred
        payment.stripe_payment_intent_id = "pi_done"
        await db.commit()

    event = {
        "id": "evt_succ",
        "type": "payment_intent.succeeded",
        "data": {"object": {"id": "pi_done"}},
    }
    async with AsyncSessionLocal() as db:
        await _handle_payment_intent_succeeded(db, event)
        await db.commit()

    payment = await _payment_for(load_id)
    assert payment.status == PaymentStatus.transferred  # not regressed to captured


async def test_account_updated_persists_capability_flags(
    client: AsyncClient, actors: dict
) -> None:
    from app.routes.webhooks import _handle_account_updated

    await _set_profile(HAULER_EMAIL, stripe_connect_account_id="acct_flags")
    event = {
        "id": "evt_acc",
        "type": "account.updated",
        "data": {
            "object": {
                "id": "acct_flags",
                "charges_enabled": True,
                "payouts_enabled": True,
                "details_submitted": True,
            }
        },
    }
    async with AsyncSessionLocal() as db:
        await _handle_account_updated(db, event)
        await db.commit()

    async with AsyncSessionLocal() as db:
        user = await db.scalar(select(User).where(User.email == HAULER_EMAIL))
        assert user.profile.stripe_charges_enabled is True
        assert user.profile.stripe_payouts_enabled is True
        assert user.profile.stripe_details_submitted is True


async def test_account_deauthorized_clears_connect_account(
    client: AsyncClient, actors: dict
) -> None:
    from app.routes.webhooks import _handle_account_deauthorized

    await _set_profile(
        HAULER_EMAIL, stripe_connect_account_id="acct_gone", stripe_charges_enabled=True
    )
    event = {
        "id": "evt_deauth",
        "type": "account.application.deauthorized",
        "account": "acct_gone",
        "data": {"object": {"id": "ca_app"}},
    }
    async with AsyncSessionLocal() as db:
        await _handle_account_deauthorized(db, event)
        await db.commit()

    async with AsyncSessionLocal() as db:
        user = await db.scalar(select(User).where(User.email == HAULER_EMAIL))
        assert user.profile.stripe_connect_account_id is None
        assert user.profile.stripe_charges_enabled is False


async def test_charge_refunded_marks_payment_refunded(
    client: AsyncClient, actors: dict
) -> None:
    from app.routes.webhooks import _handle_charge_refunded

    load_id = await _new_load(client, actors)
    await _seed_authorized_payment(load_id, pi_id="pi_ref")

    event = {
        "id": "evt_refund",
        "type": "charge.refunded",
        "data": {"object": {"id": "ch_1", "payment_intent": "pi_ref"}},
    }
    async with AsyncSessionLocal() as db:
        await _handle_charge_refunded(db, event)
        await db.commit()

    payment = await _payment_for(load_id)
    assert payment.status == PaymentStatus.refunded
    assert payment.refunded_at is not None


async def test_transfer_created_records_transfer_and_status(
    client: AsyncClient, actors: dict
) -> None:
    from app.routes.webhooks import _handle_transfer_created

    load_id = await _new_load(client, actors)
    await _seed_authorized_payment(load_id)

    event = {
        "id": "evt_transfer",
        "type": "transfer.created",
        "data": {"object": {"id": "tr_wh", "transfer_group": f"load_{load_id}"}},
    }
    async with AsyncSessionLocal() as db:
        await _handle_transfer_created(db, event)
        await db.commit()

    payment = await _payment_for(load_id)
    assert payment.stripe_transfer_id == "tr_wh"
    assert payment.status == PaymentStatus.transferred


async def test_transfer_failed_flags_error_without_status_change(
    client: AsyncClient, actors: dict
) -> None:
    from app.routes.webhooks import _handle_transfer_failed

    load_id = await _new_load(client, actors)
    await _seed_authorized_payment(load_id)

    event = {
        "id": "evt_tr_fail",
        "type": "transfer.failed",
        "data": {"object": {"id": "tr_fail", "transfer_group": f"load_{load_id}"}},
    }
    async with AsyncSessionLocal() as db:
        await _handle_transfer_failed(db, event)
        await db.commit()

    payment = await _payment_for(load_id)
    assert payment.error_message is not None
    assert payment.status == PaymentStatus.authorized  # unchanged; shipper still charged


async def test_dispute_created_flags_payment(client: AsyncClient, actors: dict) -> None:
    from app.routes.webhooks import _handle_charge_dispute_created

    load_id = await _new_load(client, actors)
    await _seed_authorized_payment(load_id, pi_id="pi_disp")

    event = {
        "id": "evt_dispute",
        "type": "charge.dispute.created",
        "data": {
            "object": {
                "id": "dp_1",
                "payment_intent": "pi_disp",
                "reason": "fraudulent",
                "amount": 1000,
            }
        },
    }
    async with AsyncSessionLocal() as db:
        await _handle_charge_dispute_created(db, event)
        await db.commit()

    payment = await _payment_for(load_id)
    assert payment.error_message is not None
    assert "Dispute" in payment.error_message


async def test_payment_intent_failed_marks_failed(client: AsyncClient, actors: dict) -> None:
    from app.routes.webhooks import _handle_payment_intent_failed

    load_id = await _new_load(client, actors)
    await _seed_authorized_payment(load_id, pi_id="pi_fail")

    event = {
        "id": "evt_fail",
        "type": "payment_intent.payment_failed",
        "data": {
            "object": {
                "id": "pi_fail",
                "last_payment_error": {"message": "Your card was declined."},
            }
        },
    }
    async with AsyncSessionLocal() as db:
        await _handle_payment_intent_failed(db, event)
        await db.commit()

    payment = await _payment_for(load_id)
    assert payment.status == PaymentStatus.failed
    assert "declined" in payment.error_message


async def test_duplicate_webhook_event_is_ignored(
    client: AsyncClient, actors: dict, monkeypatch
) -> None:
    fake_event = {
        "id": "evt_dup_1",
        "type": "payment_intent.succeeded",
        "data": {"object": {"id": "pi_unknown"}},
    }
    monkeypatch.setattr(payments, "construct_webhook_event", lambda payload, sig: fake_event)

    headers = {"Stripe-Signature": "t=1,v1=fake"}
    r1 = await client.post("/api/webhooks/stripe", headers=headers, content=b"{}")
    assert r1.status_code == 200, r1.text
    assert r1.json()["status"] == "ok"

    r2 = await client.post("/api/webhooks/stripe", headers=headers, content=b"{}")
    assert r2.status_code == 200, r2.text
    assert r2.json()["status"] == "duplicate"
