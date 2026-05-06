"""
Production-only plugin settings.

Operators usually override ``REGISTRATION_DEMOGRAPHICS_DEPARTMENTS`` here
via Tutor's ``LMS_ENV`` patch. This module reads the active Django
``settings`` and lets values flow through unchanged unless explicitly
overridden by an operator.
"""

from typing import Any

from .common import plugin_settings as common_plugin_settings


def plugin_settings(settings: Any) -> None:
    """Apply production overrides on top of the common settings."""
    common_plugin_settings(settings)
    # Production-specific overrides (if any) go here.
