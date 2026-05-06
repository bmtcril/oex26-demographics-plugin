"""
Django App Plugin configuration for registration_demographics.

This file is the contract between our plugin and `edx-platform`. Three things
make this a "plugin app" rather than a regular Django app:

1. **The `lms.djangoapp` entry point** in ``../../pyproject.toml`` —
   that's how `edx_django_utils.plugins` discovers us.
2. **The `plugin_app` dict on the AppConfig** below — declares the URL prefix
   and the settings module to merge into LMS settings.
3. **The `ready()` hook** — imports modules with side effects (filter
   pipeline registration, event receivers).

Reference: https://docs.openedx.org/projects/edx-django-utils/en/latest/plugins/how_tos/how_to_create_a_plugin_app.html
"""

from django.apps import AppConfig
from edx_django_utils.plugins.constants import PluginSettings, PluginURLs


class RegistrationDemographicsConfig(AppConfig):
    """AppConfig that wires this plugin into the LMS."""

    name = "registration_demographics"
    verbose_name = "Registration Demographics"
    default_auto_field = "django.db.models.BigAutoField"

    # ------------------------------------------------------------------
    # plugin_app: the dict edx-platform reads to integrate us.
    #
    # We register only against `lms.djangoapp` because registration only
    # happens in the LMS — see pyproject.toml for the rationale.
    # ------------------------------------------------------------------
    plugin_app = {
        PluginURLs.CONFIG: {
            "lms.djangoapp": {
                # Namespace used in `{% url %}` and `reverse()` lookups.
                PluginURLs.NAMESPACE: "registration_demographics",
                # All of our endpoints live under this prefix on the LMS.
                # E.g. /api/registration-demographics/v1/me/
                PluginURLs.REGEX: r"^api/registration-demographics/",
                # Path *inside the package* to the urls.py module.
                PluginURLs.RELATIVE_PATH: "urls",
            },
        },
        PluginSettings.CONFIG: {
            "lms.djangoapp": {
                # Loaded for every environment (devstack, production, tests).
                "common": {PluginSettings.RELATIVE_PATH: "settings.common"},
                "production": {PluginSettings.RELATIVE_PATH: "settings.production"},
                "test": {PluginSettings.RELATIVE_PATH: "settings.test"},
            },
        },
        # NOTE: We deliberately do *not* use PluginSignals.CONFIG here.
        # `ready()` below handles signal wiring instead, which keeps the
        # registration logic next to the receivers (see signals.py) and
        # makes the loading order easier to reason about during the workshop.
    }

    def ready(self):
        """
        Run plugin startup code.

        Two things must happen at app-ready time:
          1. Import ``signals`` so the ``@receiver`` decorators run and
             register handlers with Django's signal dispatcher.
          2. Import ``pipeline`` so the ``PipelineStep`` subclasses are
             defined and importable by name from
             ``OPEN_EDX_FILTERS_CONFIG`` (see ``settings/common.py``).
        """
        # Imports kept inside ready() to avoid AppRegistryNotReady errors
        # when these modules import models at top level.
        from . import (
            pipeline,  # noqa: F401 — import for side effects.
            signals,  # noqa: F401 — import for side effects.
        )
