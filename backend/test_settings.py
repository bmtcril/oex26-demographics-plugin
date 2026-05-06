"""
Minimal Django settings for running this plugin's tests outside edx-platform.

In production, edx-platform's settings module loads the plugin via the
`lms.djangoapp` entry point and our `apps.py` `plugin_app` declarations.
Here we replicate just enough of that to let tests import models and run
filters/receivers in isolation.
"""

SECRET_KEY = "registration-demographics-test-key"  # noqa: S105 — tests only

DEBUG = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
}

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.admin",
    "django.contrib.messages",
    "django.contrib.sessions",
    "rest_framework",
    "registration_demographics",
]

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

# Mirrors how edx_django_utils.plugins mounts the plugin in production:
# included with a namespace so reverse() lookups match the production paths.
ROOT_URLCONF = "tests.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# In LMS, REST_FRAMEWORK is configured by edx-platform with JWT/OAuth2/session
# auth. Our views deliberately don't override authentication_classes so they
# inherit that. For tests we set DRF defaults explicitly to mirror the
# *behaviour* of the LMS-supplied config (session-based auth works for
# `force_authenticate`).
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
    ),
}

# Mimic the plugin_settings() side effects so tests can register the filter
# without going through edx_django_utils's plugin loader.
#
# In edx-platform, plugin_settings(settings) is called with a *module* object
# so it can do attribute writes like `settings.FOO = ...`. We pass the current
# module so the writes land here as module-level globals.
import sys as _sys  # noqa: E402

from registration_demographics.settings.common import (  # noqa: E402
    plugin_settings as _plugin_settings,
)

_plugin_settings(_sys.modules[__name__])
