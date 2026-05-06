"""
Common plugin settings — applied in every environment.

This module:

* Registers ``ValidateDemographicsFields`` against the
  ``StudentRegistrationRequested`` filter so the platform invokes it during
  registration without any per-deployment wiring.
* Exposes ``REGISTRATION_DEMOGRAPHICS_DEPARTMENTS`` as the single source of
  truth for the allowed department values. Operators override this via
  Tutor's ``LMS_ENV`` patch in production.

The function is called exactly once per environment by
``edx_django_utils.plugins`` when the LMS settings module loads.
"""

from openedx_filters.learning.filters import StudentRegistrationRequested


def plugin_settings(settings):
    """Merge plugin defaults into the LMS ``settings`` module."""
    # ------------------------------------------------------------------
    # Default department allowlist. Override per-deployment via Tutor.
    # ------------------------------------------------------------------
    settings.REGISTRATION_DEMOGRAPHICS_DEPARTMENTS = ["eng", "ops", "edu"]

    # ------------------------------------------------------------------
    # Filter pipeline registration.
    #
    # We *merge* into any existing OPEN_EDX_FILTERS_CONFIG rather than
    # replacing it — other plugins may have registered their own steps on
    # the same filter, and clobbering them would be a nasty surprise.
    # ------------------------------------------------------------------
    filter_type = StudentRegistrationRequested.filter_type
    filter_config = getattr(settings, "OPEN_EDX_FILTERS_CONFIG", {}) or {}
    existing = filter_config.get(filter_type, {})
    pipeline = list(existing.get("pipeline") or [])
    step = "registration_demographics.pipeline.ValidateDemographicsFields"
    if step not in pipeline:
        pipeline.append(step)
    filter_config[filter_type] = {
        # Surface validation errors instead of swallowing them — a failed
        # demographics validation must abort registration, not silently
        # skip itself.
        "fail_silently": False,
        "pipeline": pipeline,
    }
    settings.OPEN_EDX_FILTERS_CONFIG = filter_config
