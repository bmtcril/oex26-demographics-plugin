# Backend — `registration_demographics` Django plugin

This directory is a standard Open edX **Django App Plugin**, registered via
the `lms.djangoapp` entry point in [`pyproject.toml`](./pyproject.toml).

It implements the backend half of the workshop's demographics example:

- a `LearnerDemographics` model + admin + REST API
- a filter pipeline step on `StudentRegistrationRequested`
- an event receiver for the new `RegistrationDemographicsCaptured` event
- settings wiring that registers the filter automatically when the plugin
  is installed

## Layout

```text
backend/
├── pyproject.toml          ← package metadata + lms.djangoapp entry point
├── Makefile                ← install / test / migrate convenience targets
├── manage.py               ← plugin-local Django entry (dev only)
├── test_settings.py        ← minimal settings for `pytest`
├── src/registration_demographics/
│   ├── apps.py             ← plugin_app config + ready()
│   ├── models.py           ← LearnerDemographics
│   ├── admin.py
│   ├── serializers.py
│   ├── views.py            ← DRF RetrieveUpdateAPIView (GET/PUT/PATCH /v1/me/)
│   ├── urls.py
│   ├── pipeline.py         ← openedx-filters PipelineStep
│   ├── signals.py          ← openedx-events receivers
│   ├── events.py           ← local staging ground for the
│   │                         RegistrationDemographicsCaptured event
│   │                         (the live code imports from openedx_events.learning)
│   ├── settings/
│   │   ├── common.py       ← plugin_settings() - filter registration
│   │   ├── production.py
│   │   └── test.py
│   └── migrations/
└── tests/
```

## Installing for development

Inside a `tutor dev` LMS shell:

```bash
pip install -e /openedx/backend
./manage.py lms migrate registration_demographics
```

Or, with the Tutor plugin in this repo enabled, both steps run automatically
on `tutor dev launch`.

## Running tests in isolation

```bash
make install
make test
```

This uses the in-memory SQLite settings in `test_settings.py` and does **not**
need `edx-platform` available.

## How the plugin loads

1. `pip install` registers `registration_demographics.apps:RegistrationDemographicsConfig`
   under the `lms.djangoapp` entry point.
2. On LMS startup, `edx_django_utils.plugins` discovers the entry point and
   reads `RegistrationDemographicsConfig.plugin_app` to learn:
   - what URL prefix to mount (`^api/registration-demographics/`),
   - which settings modules to merge into `lms.envs.{common,production,test}`.
3. `AppConfig.ready()` imports `signals` and `pipeline` so the
   `@receiver` decorators register and the `PipelineStep` subclass loads.
4. `settings/common.py:plugin_settings()` adds our pipeline step to
   `OPEN_EDX_FILTERS_CONFIG` so `StudentRegistrationRequested` runs it.
