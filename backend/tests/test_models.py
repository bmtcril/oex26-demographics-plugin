"""
Tests for the LearnerDemographics model.
"""

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from registration_demographics.models import LearnerDemographics


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(
        username="alice",
        email="alice@example.com",
        password="not-a-real-password",  # noqa: S106 — tests only
    )


def test_create_with_defaults(user):
    """A demographics record can be created with only the user link."""
    record = LearnerDemographics.objects.create(user=user)
    assert record.pronouns == ""
    assert record.department == ""
    assert record.created is not None
    assert record.modified is not None


def test_one_to_one_constraint(user):
    """Each user can have at most one demographics record."""
    LearnerDemographics.objects.create(user=user, pronouns="they/them")
    with pytest.raises(IntegrityError):
        LearnerDemographics.objects.create(user=user, pronouns="she/her")


def test_related_name_accessor(user):
    """The reverse accessor on User is `demographics`."""
    record = LearnerDemographics.objects.create(
        user=user,
        pronouns="they/them",
        department="eng",
    )
    assert user.demographics == record


def test_str_representation(user):
    """__str__ surfaces user_id and department for log/admin readability."""
    record = LearnerDemographics.objects.create(user=user, department="eng")
    rendered = str(record)
    assert "eng" in rendered
    assert str(user.id) in rendered


def test_str_with_blank_department(user):
    """A blank department renders as `-` rather than an empty string."""
    record = LearnerDemographics.objects.create(user=user)
    assert "dept=-" in str(record)
