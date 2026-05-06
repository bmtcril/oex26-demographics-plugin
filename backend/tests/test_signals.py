"""
Tests for the REGISTRATION_DEMOGRAPHICS_CAPTURED receiver.

We send the event end-to-end (rather than calling the receiver directly)
so the apps.ready() wiring is exercised: if signals.py isn't imported,
these tests fail.
"""

import pytest
from django.contrib.auth import get_user_model
from openedx_events.learning.data import UserData, UserPersonalData

from registration_demographics.events import (
    REGISTRATION_DEMOGRAPHICS_CAPTURED,
    RegistrationDemographicsData,
)
from registration_demographics.models import LearnerDemographics


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(
        username="alice",
        email="alice@example.com",
        password="pw",  # noqa: S106 — tests only
    )


def _user_data(user) -> UserData:
    return UserData(
        id=user.id,
        is_active=user.is_active,
        pii=UserPersonalData(
            username=user.username,
            email=user.email,
            name=user.get_full_name() or user.username,
        ),
    )


def _send(user, *, pronouns="", department=""):
    REGISTRATION_DEMOGRAPHICS_CAPTURED.send_event(
        demographics=RegistrationDemographicsData(
            user=_user_data(user),
            pronouns=pronouns,
            department=department,
        ),
    )


def test_event_creates_record(user):
    assert not LearnerDemographics.objects.filter(user=user).exists()
    _send(user, pronouns="they/them", department="eng")
    record = LearnerDemographics.objects.get(user=user)
    assert record.pronouns == "they/them"
    assert record.department == "eng"


def test_event_is_idempotent(user):
    """A second event for the same user updates the existing record."""
    _send(user, pronouns="they/them", department="eng")
    _send(user, pronouns="she/her", department="ops")
    assert LearnerDemographics.objects.filter(user=user).count() == 1
    record = LearnerDemographics.objects.get(user=user)
    assert record.pronouns == "she/her"
    assert record.department == "ops"


def test_event_handles_unknown_user(db, caplog):
    """Events for non-existent users log a warning and don't crash."""
    ghost = UserData(
        id=999_999,
        is_active=True,
        pii=UserPersonalData(username="ghost", email="g@x", name="Ghost"),
    )
    with caplog.at_level("WARNING", logger="registration_demographics.signals"):
        REGISTRATION_DEMOGRAPHICS_CAPTURED.send_event(
            demographics=RegistrationDemographicsData(
                user=ghost,
                pronouns="they/them",
                department="eng",
            ),
        )
    assert any("unknown user_id=999999" in rec.getMessage() for rec in caplog.records)
    assert LearnerDemographics.objects.count() == 0
