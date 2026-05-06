"""
Test-only root URLconf.

In a real LMS deployment, ``edx_django_utils.plugins`` calls::

    include(("registration_demographics.urls", "registration_demographics"),
            namespace="registration_demographics")

so that ``reverse("registration_demographics:me")`` works. Our isolated
tests don't go through the plugin loader, so we replicate that include here
to keep test URLs and production URLs identical.
"""

from django.urls import include, path

urlpatterns = [
    path(
        "api/registration-demographics/",
        include(
            ("registration_demographics.urls", "registration_demographics"),
            namespace="registration_demographics",
        ),
    ),
]
