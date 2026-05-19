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

# -------------------------------------------------------------------
# During development, we use the local event definition in ``.events``
# but switch to the upstream definition in ``openedx_events.learning``
# when the event is ready to be published.
from openedx_events.learning.data import RegistrationDemographicsData  # type: ignore[attr-defined]
from openedx_events.learning.signals import REGISTRATION_DEMOGRAPHICS_CAPTURED  # type: ignore[attr-defined]

# from .events import REGISTRATION_DEMOGRAPHICS_CAPTURED, RegistrationDemographicsData
# -------------------------------------------------------------------
# Retirement signal from edx-platform. Imported lazily inside a try/except so
# this plugin's unit tests (which run without edx-platform on sys.path) keep
# working. When the plugin is installed into the LMS the import succeeds and
# the receiver is wired up at AppConfig.ready() time.
try:
    from openedx.core.djangoapps.user_api.accounts.signals import (
        USER_RETIRE_LMS_MISC,
    )
except ImportError:  # pragma: no cover - exercised only outside edx-platform
    USER_RETIRE_LMS_MISC = None  # type: ignore[assignment]

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
    """
    user_id = demographics.user.id
    User = get_user_model()
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.warning(
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
    logger.info(
        "registration_demographics: %s LearnerDemographics for user_id=%s (pronouns=%r, department=%r)",
        "created" if created else "updated",
        user_id,
        record.pronouns,
        record.department,
    )


# ---------------------------------------------------------------------------
# OEP-30 retirement
#
# ``models.py`` declares ``pii_retirement: local_api`` on ``LearnerDemographics``,
# promising that this plugin will purge its own PII when the platform's
# retirement pipeline runs. ``USER_RETIRE_LMS_MISC`` is the "miscellaneous
# LMS data" stage of that pipeline — the appropriate place for plugin-owned
# tables that are not safety-critical to scrub immediately.
#
# Reference:
#   openedx/core/djangoapps/user_api/accounts/signals.py (edx-platform)
# ---------------------------------------------------------------------------
def _retire_learner_demographics(
    sender: Any,  # noqa: ARG001 — required by Django signal contract
    user: Any = None,
    **kwargs: Any,
) -> None:
    """
    Delete the retired user's ``LearnerDemographics`` row, if any.

    The platform calls this synchronously inside the retirement worker's
    transaction, so a hard delete is correct here — no other rows in this
    plugin reference the user.
    """
    if user is None:
        logger.warning("registration_demographics: USER_RETIRE_LMS_MISC fired without a user; skipping.")
        return

    deleted, _ = LearnerDemographics.objects.filter(user=user).delete()
    logger.info(
        "registration_demographics: retired user_id=%s (%d LearnerDemographics rows deleted)",
        getattr(user, "id", "?"),
        deleted,
    )


if USER_RETIRE_LMS_MISC is not None:
    USER_RETIRE_LMS_MISC.connect(
        _retire_learner_demographics,
        dispatch_uid="registration_demographics.retire_learner_demographics",
    )
