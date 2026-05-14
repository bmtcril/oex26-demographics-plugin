"""
DRF serializers for registration_demographics.

The serializer is the **single source of truth** for what a valid department
looks like. The filter pipeline step in Step 4 reuses
``validate_department`` directly so frontend POSTs and registration-time
filter checks can never disagree.
"""

from logging import getLogger

from django.conf import settings
from rest_framework import serializers

from .models import LearnerDemographics

logger = getLogger(__name__)


def validate_department(value: str) -> str:
    """
    Validate a department against the configured allowlist.

    Raises ``serializers.ValidationError`` rather than ``ValueError`` so the
    DRF layer renders a clean 400. The pipeline step in Step 4 catches the
    same exception and re-raises a filter-specific error.
    """
    logger.info("validate_department: value=%s", value)
    if value == "":
        # Empty string is allowed — department is optional.
        return value
    allowed = getattr(settings, "REGISTRATION_DEMOGRAPHICS_DEPARTMENTS", [])
    if value not in allowed:
        raise serializers.ValidationError(
            f"'{value}' is not a recognised department. "
            f"Choose one of: {', '.join(allowed) or '(no departments configured)'}."
        )
    return value


class LearnerDemographicsSerializer(serializers.ModelSerializer):
    """Public representation of a learner's demographics record."""

    class Meta:
        model = LearnerDemographics
        fields = ("pronouns", "department", "created", "modified")
        read_only_fields = ("created", "modified")

    def validate_department(self, value: str) -> str:  # noqa: D401 — DRF hook
        """DRF field-level validator delegating to module-level function."""
        return validate_department(value)
