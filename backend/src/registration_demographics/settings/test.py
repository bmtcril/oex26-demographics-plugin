"""
Test-only plugin settings.

Consumed by edx-platform's test settings module via the plugin loader.
``test_settings.py`` at the repo root uses ``common.plugin_settings``
directly; this module exists so the LMS test environment loads us too.
"""

from typing import Any

from .common import plugin_settings as common_plugin_settings


def plugin_settings(settings: Any) -> None:
    """Apply test overrides on top of the common settings."""
    common_plugin_settings(settings)
    # Tests should use a deterministic, small department list.
    settings.REGISTRATION_DEMOGRAPHICS_DEPARTMENTS = ["eng", "ops", "edu"]
