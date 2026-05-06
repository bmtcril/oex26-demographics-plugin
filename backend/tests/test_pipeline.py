"""
Tests for the ValidateDemographicsFields filter pipeline step.

We exercise the step in two ways:

1. **Direct unit tests** — instantiate the step and call ``run_filter()``
   to lock down the validation/normalisation contract.
2. **Pipeline integration test** — run the full ``StudentRegistrationRequested``
   filter to prove that ``settings.OPEN_EDX_FILTERS_CONFIG`` actually wires
   our step into the platform's pipeline runner.
"""

import pytest
from django.http import QueryDict
from openedx_filters.learning.filters import StudentRegistrationRequested

from registration_demographics.pipeline import ValidateDemographicsFields


def _make_step():
    return ValidateDemographicsFields(
        filter_type=StudentRegistrationRequested.filter_type,
        running_pipeline=[
            "registration_demographics.pipeline.ValidateDemographicsFields",
        ],
    )


def _qd(**kwargs) -> QueryDict:
    """Build an immutable QueryDict from kwargs (matches the platform shape)."""
    qd = QueryDict(mutable=True)
    for key, value in kwargs.items():
        qd[key] = value
    qd._mutable = False  # type: ignore[attr-defined]
    return qd


# ---------------------------------------------------------------------------
# Direct unit tests on the PipelineStep
# ---------------------------------------------------------------------------


def test_passes_through_when_fields_absent():
    """The step is a no-op if neither demographic field is present."""
    step = _make_step()
    form = _qd(username="alice", email="alice@example.com")
    result = step.run_filter(form)
    assert result == {"form_data": form}


def test_normalises_pronouns_whitespace():
    step = _make_step()
    form = _qd(pronouns="  they/them  ", department="eng")
    result = step.run_filter(form)
    assert result["form_data"]["pronouns"] == "they/them"
    # Original immutable QueryDict is not mutated.
    assert form["pronouns"] == "  they/them  "


def test_accepts_valid_department():
    step = _make_step()
    form = _qd(department="eng")
    result = step.run_filter(form)
    assert result["form_data"]["department"] == "eng"


def test_accepts_blank_department():
    step = _make_step()
    form = _qd(department="")
    result = step.run_filter(form)
    assert result["form_data"]["department"] == ""


def test_rejects_unknown_department():
    step = _make_step()
    form = _qd(department="does-not-exist")
    with pytest.raises(StudentRegistrationRequested.PreventRegistration) as excinfo:
        step.run_filter(form)
    assert "does-not-exist" in str(excinfo.value)


def test_prevent_registration_carries_error_code():
    step = _make_step()
    form = _qd(department="bogus")
    with pytest.raises(StudentRegistrationRequested.PreventRegistration) as excinfo:
        step.run_filter(form)
    # The MFE uses error_code to map the message back to the right field.
    assert getattr(excinfo.value, "error_code", None) == "invalid_department"


# ---------------------------------------------------------------------------
# Integration test through the StudentRegistrationRequested filter runner
# ---------------------------------------------------------------------------


def test_filter_runner_invokes_our_step():
    """settings.OPEN_EDX_FILTERS_CONFIG actually wires us into the pipeline."""
    form = _qd(pronouns="  she/her  ", department="eng")
    result = StudentRegistrationRequested.run_filter(form_data=form)
    # The runner returns the (possibly mutated) form_data from the last step.
    assert result["pronouns"] == "she/her"


def test_filter_runner_aborts_on_invalid_department():
    form = _qd(department="invalid")
    with pytest.raises(StudentRegistrationRequested.PreventRegistration):
        StudentRegistrationRequested.run_filter(form_data=form)
