"""
Tests for the DemographicsMeView REST endpoint.

Covers the contract the frontend depends on:

* Anonymous GET is rejected.
* Authenticated GET auto-creates an empty record.
* PATCH updates fields and returns the new state.
* Department values outside the configured allowlist are rejected.
* The endpoint is hard-scoped to ``request.user`` — there is no way to
  read another user's record.
"""

import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient

from registration_demographics.models import LearnerDemographics


@pytest.fixture
def user(db: None) -> User:
    return User.objects.create_user(
        username="alice",
        email="alice@example.com",
        password="pw",  # noqa: S106 — tests only
    )


@pytest.fixture
def other_user(db: None) -> User:
    return User.objects.create_user(
        username="bob",
        email="bob@example.com",
        password="pw",  # noqa: S106 — tests only
    )


@pytest.fixture
def client() -> APIClient:
    return APIClient()


@pytest.fixture
def me_url() -> str:
    return reverse("registration_demographics:me")


def test_anonymous_get_rejected(client: APIClient, me_url: str) -> None:
    response = client.get(me_url)
    assert response.status_code in (401, 403)


def test_authenticated_get_autocreates_empty_record(
    client: APIClient, user: User, me_url: str
) -> None:
    assert not LearnerDemographics.objects.filter(user=user).exists()
    client.force_authenticate(user=user)
    response = client.get(me_url)
    assert response.status_code == 200
    assert response.data["pronouns"] == ""
    assert response.data["department"] == ""
    assert LearnerDemographics.objects.filter(user=user).exists()


def test_patch_updates_fields(client: APIClient, user: User, me_url: str) -> None:
    client.force_authenticate(user=user)
    client.get(me_url)  # ensure record exists
    response = client.patch(
        me_url,
        {"pronouns": "they/them", "department": "eng"},
        format="json",
    )
    assert response.status_code == 200
    assert response.data["pronouns"] == "they/them"
    assert response.data["department"] == "eng"
    record = LearnerDemographics.objects.get(user=user)
    assert record.pronouns == "they/them"
    assert record.department == "eng"


def test_patch_rejects_unknown_department(
    client: APIClient, user: User, me_url: str
) -> None:
    client.force_authenticate(user=user)
    response = client.patch(
        me_url,
        {"department": "not-a-real-department"},
        format="json",
    )
    assert response.status_code == 400
    assert "department" in response.data


def test_patch_accepts_blank_department(
    client: APIClient, user: User, me_url: str
) -> None:
    client.force_authenticate(user=user)
    response = client.patch(me_url, {"department": ""}, format="json")
    assert response.status_code == 200


def test_endpoint_scoped_to_request_user(
    client: APIClient, user: User, other_user: User, me_url: str
) -> None:
    """One user's PATCH must not leak into another user's record."""
    LearnerDemographics.objects.create(user=other_user, pronouns="she/her")
    client.force_authenticate(user=user)
    response = client.patch(me_url, {"pronouns": "they/them"}, format="json")
    assert response.status_code == 200
    other_user.refresh_from_db()
    assert other_user.demographics.pronouns == "she/her"  # type: ignore[attr-defined]
