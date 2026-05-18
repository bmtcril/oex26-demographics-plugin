"""
``RegistrationDemographicsCaptured`` event definition.

**NOT ACTUALLY USED, see below.**

----------------------------------------------------------------------------
**Where this lives long-term:**
This module is the *staging ground* for the event definition. The intent is
to migrate it upstream into ``openedx_events.learning`` (see
``upstream-patches/openedx-events.patch``) so any plugin can subscribe
without depending on this package. While the upstream PR is in flight, the
event lives here so the demographics plugin and its tests work today.

The ``event_type`` string is fixed (``org.openedx...v1``) so receivers
written against the eventual upstream version will continue to match the
same Django signal even before the migration lands.
----------------------------------------------------------------------------

The workshop uses this file as a sample for showing the staging ground for
"defining a new event" but the actual functional code being used comes from
the ``openedx_events.learning`` package.
"""

from __future__ import annotations

import attr
from openedx_events.learning.data import UserData
from openedx_events.tooling import OpenEdxPublicSignal


@attr.s(frozen=True)
class RegistrationDemographicsData:
    """
    Payload for ``REGISTRATION_DEMOGRAPHICS_CAPTURED``.

    Carries the just-registered user (so receivers can foreign-key against
    them) and the validated demographic fields. ``pronouns`` and
    ``department`` are deliberately strings, not enums — the department
    allowlist is operator-configurable and pronouns are free-text.
    """

    user: UserData = attr.ib()
    pronouns: str = attr.ib(default="")
    department: str = attr.ib(default="")


REGISTRATION_DEMOGRAPHICS_CAPTURED = OpenEdxPublicSignal(
    event_type="org.openedx.learning.student.registration.demographics.captured.v1",
    data={
        "demographics": RegistrationDemographicsData,
    },
)
