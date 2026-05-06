"""
Database models for registration_demographics.

The single model, ``LearnerDemographics``, stores the additional fields
collected during registration. It is intentionally minimal — the workshop's
focus is the *plumbing* between the MFE, the filter, the event, and this
model, not the model itself.

Design decisions worth surfacing:

* **Department choices live in settings, not on the field.**
  ``CharField(choices=...)`` would bake the choice list into migrations,
  which fights the "operators customize departments via Tutor" story.
  Instead, we keep the field a plain ``CharField`` and validate the value
  against ``settings.REGISTRATION_DEMOGRAPHICS_DEPARTMENTS`` in the filter
  pipeline step (Step 4) and the DRF serializer (Step 3).

* **One demographics record per user.**
  We use ``OneToOneField`` rather than ``ForeignKey``. A learner has exactly
  one current set of demographics; history would be a separate model.

* **PII annotations** follow OEP-30 so this plugin can opt-in to the
  platform-wide retirement pipeline without further work.
"""

from django.conf import settings
from django.db import models


class LearnerDemographics(models.Model):
    """
    Additional demographic information captured at registration time.

    .. pii: Stores user-supplied pronouns and an optional department
            affiliation. Both are user-identifying when combined with the
            ``user`` foreign key.
    .. pii_types: other
    .. pii_retirement: local_api
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="demographics",
        help_text="The learner whose demographics these are.",
    )

    # Free-text on purpose: any closed list would be insufficient and
    # exclusionary. The MFE field is also free-text with helper examples.
    pronouns = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="Self-identified pronouns, e.g. 'she/her', 'they/them'.",
    )

    # Validated against settings.REGISTRATION_DEMOGRAPHICS_DEPARTMENTS in the
    # filter and serializer; see module docstring for rationale.
    department = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text=(
            "Department affiliation key. Validated against "
            "settings.REGISTRATION_DEMOGRAPHICS_DEPARTMENTS."
        ),
    )

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Learner demographics"
        verbose_name_plural = "Learner demographics"

    def __str__(self) -> str:
        return (
            f"LearnerDemographics(user={self.user_id}, dept={self.department or '-'})"  # type: ignore[attr-defined]
        )
