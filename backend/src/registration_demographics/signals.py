"""
Event receivers for registration_demographics.

We listen for the new ``REGISTRATION_DEMOGRAPHICS_CAPTURED`` event (defined
in ``.events``, destined for ``openedx-events`` upstream) and persist the
payload to the ``LearnerDemographics`` model.

Why a receiver and not a synchronous write in the registration view?

* Events fire **after** the platform has decided the registration succeeded.
  If anything goes wrong here, the user account already exists — so we
  swallow exceptions with a structured log line rather than letting them
  bubble up and confuse the registration view.
* Event-bus relay (Kafka/Redis) can be added later without touching this
  receiver — that's the whole point of using events instead of direct calls.
"""

from __future__ import annotations

import logging
from typing import Any

from django.contrib.auth import get_user_model
from django.dispatch import receiver

from .events import REGISTRATION_DEMOGRAPHICS_CAPTURED, RegistrationDemographicsData
from .models import LearnerDemographics

log = logging.getLogger(__name__)


@receiver(REGISTRATION_DEMOGRAPHICS_CAPTURED)
def persist_registration_demographics(
    sender: Any,  # noqa: ARG001 — required by Django signal contract
    demographics: RegistrationDemographicsData,
    **kwargs: Any,
) -> None:
    """
    Persist a ``RegistrationDemographicsData`` payload to the database.

    Idempotent: if a record already exists for this user, fields are updated
    rather than duplicated. This protects against duplicate event delivery
    (e.g. once the event bus is wired up).
    """
    user_id = demographics.user.id
    User = get_user_model()
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        log.warning(
            "registration_demographics: dropping event for unknown user_id=%s",
            user_id,
        )
        return

    record, created = LearnerDemographics.objects.update_or_create(
        user=user,
        defaults={
            "pronouns": demographics.pronouns or "",
            "department": demographics.department or "",
        },
    )
    log.info(
        "registration_demographics: %s LearnerDemographics for user_id=%s "
        "(pronouns=%r, department=%r)",
        "created" if created else "updated",
        user_id,
        record.pronouns,
        record.department,
    )
