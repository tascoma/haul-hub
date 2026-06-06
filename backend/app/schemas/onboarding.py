from typing import Literal

from pydantic import BaseModel

OnboardingStep = Literal[
    "profile",
    "hauler_profile",
    "hauler_vehicle",
    "hauler_service_area",
    "done",
]


class OnboardingChecks(BaseModel):
    has_vehicle: bool
    has_service_area: bool


class OnboardingStatus(BaseModel):
    profile_complete: bool
    customer_ready: bool
    hauler_ready: bool
    next_step: OnboardingStep
    checks: OnboardingChecks
