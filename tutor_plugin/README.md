# Tutor Plugin — Registration Demographics

This directory contains the Tutor plugin (`tutor-contrib-demographics-plugin`) that wires the registration demographics feature into a Tutor-managed Open edX deployment.

## Table of Contents

- [What This Plugin Does](#what-this-plugin-does)
- [Requirements](#requirements)
- [Installation](#installation)
- [Development Setup](#development-setup)
- [Production Setup](#production-setup)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

---

## What This Plugin Does

| Layer | What gets wired |
|-------|-----------------|
| **Backend** | Installs `openedx-registration-demographics-plugin` into the LMS Docker image. The Django app registers itself as an `lms.djangoapp` entry point, adding the `LearnerDemographics` model, the `StudentRegistrationRequested` filter step, the `REGISTRATION_DEMOGRAPHICS_CAPTURED` event receiver, and the `/api/registration-demographics/v1/me/` REST endpoint. |
| **Migrations** | Runs `./manage.py lms migrate registration_demographics` on `tutor … init` so the `LearnerDemographics` table is created automatically. |
| **Frontend** | *(requires `tutor-mfe`)* Installs `openedx-demographics-plugin` into all MFE images, imports `DemographicsFields` into `env.config.jsx`, and registers it against the `org.openedx.frontend.authn.register.additional_fields.v1` plugin slot in `frontend-app-authn`. If `tutor-mfe` is not installed the backend half still works — the plugin degrades gracefully. |

The frontend slot is empty by default (no built-in widget to replace), so the plugin uses a plain `PLUGIN_OPERATIONS.Insert`. Compare with `tutor-contrib-sample-plugin`, which uses `Hide` + `Insert` because it replaces an existing default widget.

---

## Requirements

- **Tutor** ≥ 20.0.0
- **tutor-mfe** — optional, needed for the frontend registration-form fields

---

## Installation

### Install the Tutor plugin package

```bash
# From this repository (development / workshop)
pip install -e .

# If published to PyPI (production)
pip install tutor-contrib-demographics-plugin
```

### Enable the plugin

```bash
tutor plugins enable demographics_plugin
tutor plugins list   # verify it appears
```

---

## Development Setup

Use this workflow when iterating on the backend Django plugin source locally.

### 1. Mount the backend source

```bash
# From the repo root — maps ./backend into the openedx container's virtualenv
tutor mounts add ./backend
tutor mounts list   # should show: openedx <= .../backend
```

The `MOUNTED_DIRECTORIES` entry in `plugin.py` makes this work; without it the mount is ignored.

### 2. Launch (or restart) the dev environment

```bash
tutor dev launch
# or, if already running:
tutor dev stop && tutor dev start
```

### 3. Run migrations

```bash
tutor dev run lms ./manage.py lms migrate registration_demographics
```

### 4. Verify the backend

```bash
tutor dev exec lms ./manage.py lms shell -c "
from registration_demographics.models import LearnerDemographics
print('Model loaded OK, table exists:', LearnerDemographics.objects.count() >= 0)
"
```

### 5. Verify the frontend slot (requires tutor-mfe)

Navigate to the registration page in your browser. The **Pronouns** text field and **Department** select should appear just above the Create Account button.

If the fields are missing, check the browser console for a `ReferenceError: DemographicsFields is not defined` — that means the `mfe-env-config-buildtime-imports` patch didn't apply, usually because the MFE image was not rebuilt after enabling the plugin. Rebuild with:

```bash
tutor images build mfe
tutor dev restart mfe
```

---

## Production Setup

### 1. Install and enable

```bash
pip install tutor-contrib-demographics-plugin
tutor plugins enable demographics_plugin
```

### 2. Build images

The `openedx-lms-dockerfile-post-python-requirements` patch installs the backend package into the LMS image at build time. The `mfe-dockerfile-post-npm-install` patch installs the npm package into all MFE images.

```bash
tutor images build openedx   # LMS image with backend plugin
tutor images build mfe       # MFE images with frontend plugin (if using tutor-mfe)
```

### 3. Deploy

```bash
tutor local launch
```

Migrations run automatically during `launch` / `init` as the backend package is installed into the LMS virtual environment.

### 4. Verify

```bash
# Backend — check the model exists
tutor local exec lms ./manage.py lms showmigrations registration_demographics

# REST API — should return 200 with an empty demographics record for the user
curl -H "Authorization: Bearer <jwt>" \
  https://<your-lms-domain>/api/registration-demographics/v1/me/
```

---

## Configuration

### Customising the department list

The backend validates the `department` field against `settings.REGISTRATION_DEMOGRAPHICS_DEPARTMENTS`. Add an LMS environment patch to your Tutor config to override the default:

```python
# In your own Tutor plugin or tutor_config.yml patch
hooks.Filters.ENV_PATCHES.add_item((
    "openedx-lms-common-settings",
    """
REGISTRATION_DEMOGRAPHICS_DEPARTMENTS = [
    "engineering",
    "operations",
    "education",
    "finance",
]
""",
))
```

The frontend `DemographicsFields` component accepts a `departments` prop (array of `{value, label}` objects). Pass it via `pluginProps` when registering the slot if you want the dropdown labels to differ from the backend keys:

```python
PLUGIN_SLOTS.add_item((
    "authn",
    "org.openedx.frontend.authn.register.additional_fields.v1",
    """
    {
      op: PLUGIN_OPERATIONS.Insert,
      widget: {
        id: 'demographics_fields',
        type: DIRECT_PLUGIN,
        priority: 50,
        RenderWidget: DemographicsFields,
        pluginProps: {
          departments: [
            { value: 'engineering', label: 'Engineering' },
            { value: 'operations', label: 'Operations' },
            { value: 'education', label: 'Education' },
            { value: 'finance', label: 'Finance' },
          ],
        },
      },
    }""",
))
```

Keep the `value` strings in sync with `REGISTRATION_DEMOGRAPHICS_DEPARTMENTS` or the backend filter will reject them.

---

## Troubleshooting

### Plugin not listed after `tutor plugins list`

```bash
# Confirm the package installed into the same Python env as tutor
pip show tutor-contrib-demographics-plugin
tutor plugins printroot   # local-file plugins live here; pip-installed ones auto-discover
```

### Backend plugin not found in LMS

```bash
# Confirm the patch applied during the image build
tutor images build openedx --no-cache 2>&1 | grep demographics

# Manual check inside the running container
tutor dev exec lms pip show openedx-registration-demographics-plugin
```

### Frontend fields not appearing

1. Confirm `tutor-mfe` is installed: `pip show tutor-mfe`
2. Rebuild the MFE image: `tutor images build mfe`
3. Check the browser console for `ReferenceError` or `slot … not found` errors
4. Confirm `env.config.jsx` contains the import:

```bash
tutor dev exec authn cat /openedx/app/env.config.jsx | grep DemographicsFields
```

### Migrations not applied

```bash
tutor dev run lms ./manage.py lms showmigrations registration_demographics
# If 0001_initial shows [ ]:
tutor dev run lms ./manage.py lms migrate registration_demographics
```

### Department validation errors at registration

The `department` value submitted by the frontend must exactly match one of the strings in `REGISTRATION_DEMOGRAPHICS_DEPARTMENTS`. Check the setting is applied in the running container:

```bash
tutor dev exec lms ./manage.py lms shell -c "
from django.conf import settings
print(getattr(settings, 'REGISTRATION_DEMOGRAPHICS_DEPARTMENTS', 'NOT SET'))
"
```
