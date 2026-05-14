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

from django.db.utils import IntegrityError
from django.dispatch import receiver

# -------------------------------------------------------------------
# During development, we use the local event definition in ``.events``
# but switch to the upstream definition in ``openedx_events.learning``
# when the event is ready to be published.
from openedx_events.learning.data import RegistrationDemographicsData
from openedx_events.learning.signals import REGISTRATION_DEMOGRAPHICS_CAPTURED

# from .events import REGISTRATION_DEMOGRAPHICS_CAPTURED, RegistrationDemographicsData
# -------------------------------------------------------------------
from .models import LearnerDemographics

logger = logging.getLogger(__name__)


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
    (e.g. if events are coming from different places, or the event bus).

    Perf note: There is an argument to be made that we should make another
    query here to confirm the existence of the user, but the upsert will
    failif the user does not exist, so we can rely on that exception and
    save the round trip.
    """
    try:
        record, created = LearnerDemographics.objects.update_or_create(
            user_id=demographics.user.id,
            defaults={
                "pronouns": demographics.pronouns or "",
                "department": demographics.department or "",
            },
        )
        logger.info(
            "registration_demographics: %s LearnerDemographics for user_id=%s (pronouns=%r, department=%r)",
            "created" if created else "updated",
            demographics.user.id,
            record.pronouns,
            record.department,
        )
    except IntegrityError:
        logger.warning(
            "registration_demographics: dropping event for unknown user_id=%s",
            demographics.user.id,
        )
        return
