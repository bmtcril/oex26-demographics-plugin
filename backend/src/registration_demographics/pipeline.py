"""
openedx-filters pipeline steps for registration_demographics.

Hooks into ``StudentRegistrationRequested`` (filter type
``org.openedx.learning.student.registration.requested.v1``) to validate the
two new demographic fields submitted by the registration MFE.

Filter contract recap:

    run_filter(self, form_data: QueryDict) -> dict | QueryDict | None

* Return a dict / QueryDict to continue the pipeline with that data.
* Raise ``StudentRegistrationRequested.PreventRegistration`` to abort.

The validation logic lives in ``serializers.validate_department`` so the
REST API in ``views.py`` and this filter share **one** source of truth
about what a valid department is. If you change the rules, change them
there.
"""

from logging import getLogger
from typing import Any

from django.http import QueryDict
from openedx_filters.filters import PipelineStep
from openedx_filters.learning.filters import StudentRegistrationRequested
from rest_framework import serializers as drf_serializers

from .serializers import validate_department

logger = getLogger(__name__)


class ValidateDemographicsFields(PipelineStep):
    """
    Validate ``pronouns`` and ``department`` on the registration form.

    Configured in ``OPEN_EDX_FILTERS_CONFIG`` under
    ``org.openedx.learning.student.registration.requested.v1`` (see
    ``settings/common.py``).
    """

    def run_filter(self, form_data: QueryDict, *args: Any, **kwargs: Any) -> dict[str, Any]:  # type: ignore[override]
        """
        Validate and normalise the demographic form fields in-place.

        Args:
            form_data: the QueryDict of registration form fields submitted
                by the MFE. May or may not contain ``pronouns``/``department``
                depending on whether the operator has enabled the slot.

        Returns:
            ``{"form_data": form_data}`` so the platform's pipeline runner
            propagates our (possibly mutated) copy to the next step.
        """
        logger.info("run_filter: form_data=%s", form_data)
        # Whitespace-normalise pronouns. Free-text input plus default
        # autocomplete behaviour means leading/trailing whitespace is common
        # and harmless; persisting it would just look ugly in admin.
        pronouns = (form_data.get("pronouns") or "").strip()
        if pronouns != form_data.get("pronouns", ""):
            # QueryDict is immutable on the request; copy before mutating.
            form_data = form_data.copy()
            form_data["pronouns"] = pronouns

        # Validate the department against the configured allowlist. Reusing
        # the serializer's validator means any future change to that list's
        # semantics is honoured here automatically.
        department = form_data.get("department", "")
        try:
            logger.info("validate_department: department=%s", department)
            validate_department(department)
        except drf_serializers.ValidationError as exc:
            # PreventRegistration takes a single human-readable message and
            # an optional structured `redirect_to`/`error_code`. We surface
            # the field name in `error_code` so MFE error handling can map
            # it back to the right form field.
            raise StudentRegistrationRequested.PreventRegistration(
                _flatten_validation_message(exc),
                error_code="invalid_department",
            ) from exc

        return {"form_data": form_data}


def _flatten_validation_message(exc: drf_serializers.ValidationError) -> str:
    """Render a DRF ValidationError as a single user-facing string."""
    detail = exc.detail
    if isinstance(detail, list):
        return " ".join(str(item) for item in detail)
    return str(detail)
