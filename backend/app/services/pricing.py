from app.core.config import settings
from app.models.load import Urgency


def calculate_price_cents(*, distance_miles: float, weight_lbs: int, urgency: Urgency) -> int:
    """Platform-calculated haul price. Tune the rates in app.core.config.Settings."""
    subtotal = (
        settings.price_base_cents
        + settings.price_per_mile_cents * distance_miles
        + settings.price_weight_surcharge_per_100lb_cents * (weight_lbs / 100)
    )
    multiplier = settings.price_express_multiplier if urgency is Urgency.express else 1.0
    return int(round(subtotal * multiplier))
