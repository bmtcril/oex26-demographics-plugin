"""
Tests for the REGISTRATION_DEMOGRAPHICS_CAPTURED receiver.

We send the event end-to-end (rather than calling the receiver directly)
so the apps.ready() wiring is exercised: if signals.py isn't imported,
these tests fail.
"""

import pytest
from django.contrib.auth.models import User
from openedx_events.learning.data import (
    RegistrationDemographicsData,  # type: ignore[attr-defined]
    UserData,
    UserPersonalData,
)
from openedx_events.learning.signals import REGISTRATION_DEMOGRAPHICS_CAPTURED  # type: ignore[attr-defined]

from registration_demographics.models import LearnerDemographics


@pytest.fixture
def user(db: None) -> User:
    return User.objects.create_user(
        username="alice",
        email="alice@example.com",
        password="pw",  # noqa: S106 — tests only
    )


def _user_data(user: User) -> UserData:
    # UserData/UserPersonalData use old-style attr.ib(type=...) — pyright can't
    # see their constructor parameters; positional args + type: ignore per line.
    pii = UserPersonalData(user.username, user.email, user.get_full_name() or user.username)  # type: ignore
    return UserData(user.pk, user.is_active, pii)  # type: ignore


def _send(user: User, *, pronouns: str = "", department: str = "") -> None:
    REGISTRATION_DEMOGRAPHICS_CAPTURED.send_event(
        demographics=RegistrationDemographicsData(
            user=_user_data(user),
            pronouns=pronouns,
            department=department,
        ),
    )


def test_event_creates_record(user: User) -> None:
    assert not LearnerDemographics.objects.filter(user=user).exists()
    _send(user, pronouns="they/them", department="eng")
    record = LearnerDemographics.objects.get(user=user)
    assert record.pronouns == "they/them"
    assert record.department == "eng"


def test_event_is_idempotent(user: User) -> None:
    """A second event for the same user updates the existing record."""
    _send(user, pronouns="they/them", department="eng")
    _send(user, pronouns="she/her", department="ops")
    assert LearnerDemographics.objects.filter(user=user).count() == 1
    record = LearnerDemographics.objects.get(user=user)
    assert record.pronouns == "she/her"
    assert record.department == "ops"


def test_event_handles_unknown_user(db: None, caplog: pytest.LogCaptureFixture) -> None:
    """Events for non-existent users log a warning and don't crash."""
    ghost_pii = UserPersonalData("ghost", "g@x", "Ghost")  # type: ignore
    ghost = UserData(999_999, True, ghost_pii)  # type: ignore
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
