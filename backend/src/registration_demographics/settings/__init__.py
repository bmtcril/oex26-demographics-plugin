"""
Plugin settings package.

Each module defines a ``plugin_settings(settings)`` function that
``edx_django_utils.plugins`` calls when the LMS settings module loads:

* ``common.py`` — applied in every environment.
* ``production.py`` — production-only overrides.
* ``test.py`` — test-only overrides.

See ``apps.py``'s ``PluginSettings.CONFIG`` for the wiring.
"""
