"""
REST API views for registration_demographics.

We expose a single endpoint, ``/v1/me/``, returning the authenticated user's
demographics record. Auto-creating on first GET keeps the frontend simple:
no 404 path to handle, just a record that may have empty fields.

Permissions: ``IsAuthenticated`` is sufficient because the queryset is
implicitly scoped to ``request.user`` in ``get_object()``. There is no way
for one learner to read another learner's record through this view, so we
don't need the ``IsOwnerOrStaffSuperuser`` machinery sample-plugin uses.

**Authentication is deliberately not overridden.** A plugin should inherit
the platform's ``REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"]`` (JWT,
OAuth2, session) so deployments don't have to re-discover their auth setup.
The test suite injects ``SessionAuthentication`` via ``test_settings.py``.
"""

from rest_framework import generics, permissions

from .models import LearnerDemographics
from .serializers import LearnerDemographicsSerializer


class DemographicsMeView(generics.RetrieveUpdateAPIView):
    """GET / PUT / PATCH the authenticated user's demographics record."""

    serializer_class = LearnerDemographicsSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self) -> LearnerDemographics:
        """Return the current user's record, creating an empty one if needed."""
        record, _created = LearnerDemographics.objects.get_or_create(
            user=self.request.user,
        )
        return record
