"""
URL configuration mounted by edx-platform under ``/api/registration-demographics/``.

The current public surface area is a single endpoint::

    GET    /api/registration-demographics/v1/me/
    PUT    /api/registration-demographics/v1/me/
    PATCH  /api/registration-demographics/v1/me/

All scoped to ``request.user`` — see ``views.DemographicsMeView``.
"""

from django.urls import path

from .views import DemographicsMeView

app_name = "registration_demographics"

urlpatterns = [
    path("v1/me/", DemographicsMeView.as_view(), name="me"),
]
