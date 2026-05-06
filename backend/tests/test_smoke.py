"""
Smoke tests for the plugin package.

These run before the model/filter/event work in Steps 2–7 and serve as a
build-plan tripwire: if these break, we've regressed something foundational
about how the plugin loads.
"""


def test_app_config_importable():
    """The AppConfig must import without side effects beyond Django app loading."""
    from registration_demographics.apps import RegistrationDemographicsConfig

    assert RegistrationDemographicsConfig.name == "registration_demographics"
    assert "lms.djangoapp" in RegistrationDemographicsConfig.plugin_app["url_config"]


def test_plugin_settings_applied():
    """plugin_settings() should populate the departments default."""
    from django.conf import settings

    assert settings.REGISTRATION_DEMOGRAPHICS_DEPARTMENTS == ["eng", "ops", "edu"]


def test_urls_module_importable():
    """The urls module must be importable at plugin-load time."""
    from registration_demographics import urls

    assert hasattr(urls, "urlpatterns")
