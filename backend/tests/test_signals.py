"""
Tests for the REGISTRATION_DEMOGRAPHICS_CAPTURED receiver.

We send the event end-to-end (rather than calling the receiver directly)
so the apps.ready() wiring is exercised: if signals.py isn't imported,
these tests fail.
"""

import pytest
from django.contrib.auth.models import User
from django.dispatch import Signal
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


# ---------------------------------------------------------------------------
# USER_RETIRE_LMS_MISC retirement receiver
#
# The real signal lives in ``openedx.core.djangoapps.user_api.accounts.signals``
# and is not importable when running these tests in isolation, so signals.py
# guards the import and sets ``USER_RETIRE_LMS_MISC = None`` in that case. To
# exercise the receiver itself we monkeypatch a local ``Signal()`` into the
# module, connect the receiver to it, and send manually.
# ---------------------------------------------------------------------------


@pytest.fixture
def retire_signal(monkeypatch: pytest.MonkeyPatch) -> Signal:
    """Install a local ``Signal`` in place of edx-platform's and wire up the receiver."""
    from registration_demographics import signals as plugin_signals

    sig = Signal()
    monkeypatch.setattr(plugin_signals, "USER_RETIRE_LMS_MISC", sig)
    sig.connect(
        plugin_signals._retire_learner_demographics,
        dispatch_uid="test.retire_learner_demographics",
    )
    return sig


def test_retirement_deletes_user_row(user: User, retire_signal: Signal) -> None:
    LearnerDemographics.objects.create(user=user, pronouns="they/them", department="eng")
    retire_signal.send(sender=None, user=user)
    assert not LearnerDemographics.objects.filter(user=user).exists()


def test_retirement_is_a_noop_when_no_row_exists(user: User, retire_signal: Signal) -> None:
    assert not LearnerDemographics.objects.filter(user=user).exists()
    retire_signal.send(sender=None, user=user)  # must not raise
    assert not LearnerDemographics.objects.filter(user=user).exists()


def test_retirement_only_deletes_the_target_user(retire_signal: Signal, db: None) -> None:
    alice = User.objects.create_user(username="alice2", email="a2@x", password="pw")  # noqa: S106
    bob = User.objects.create_user(username="bob", email="b@x", password="pw")  # noqa: S106
    LearnerDemographics.objects.create(user=alice, pronouns="they/them", department="eng")
    LearnerDemographics.objects.create(user=bob, pronouns="she/her", department="ops")

    retire_signal.send(sender=None, user=alice)

    assert not LearnerDemographics.objects.filter(user=alice).exists()
    assert LearnerDemographics.objects.filter(user=bob).exists()


def test_retirement_without_user_logs_and_skips(
    retire_signal: Signal,
    caplog: pytest.LogCaptureFixture,
    db: None,
) -> None:
    with caplog.at_level("WARNING", logger="registration_demographics.signals"):
        retire_signal.send(sender=None, user=None)
    assert any("fired without a user" in rec.getMessage() for rec in caplog.records)
