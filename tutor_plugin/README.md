# Tutor Plugin — Registration Demographics

This directory contains the Tutor plugin (`tutor-contrib-demographics-plugin`) that wires the registration demographics feature into a Tutor-managed Open edX deployment.

## Table of Contents

- [What This Plugin Does](#what-this-plugin-does)
- [Requirements](#requirements)
- [Installation](#installation)
- [Development Setup](#development-setup)
- [Production Setup (aspirational)](#production-setup-aspirational)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

---

## What This Plugin Does

The plugin as shipped is configured for the **development / workshop flow**: it relies on local sibling checkouts of `backend/`, `frontend-app-authn`, and friends being mounted via `tutor mounts`. The build-time patches that would replace those mounts in production are present in [`tutordemographicsplugin/plugin.py`](./tutordemographicsplugin/plugin.py) but commented out - see [Production Setup](#production-setup-aspirational) for how to enable them.

| Layer | What gets wired (current dev default) |
|-------|---------------------------------------|
| **Backend** | Adds `("openedx", "backend")` to `MOUNTED_DIRECTORIES` so `tutor mounts add ./backend` maps this repo's Django app into the LMS container's virtualenv as an editable install. The app self-registers as an `lms.djangoapp` entry point, adding the `LearnerDemographics` model, the `StudentRegistrationRequested` filter step, the `REGISTRATION_DEMOGRAPHICS_CAPTURED` event receiver, and the `/api/registration-demographics/v1/me/` REST endpoint. |
| **Migrations** | Run automatically as part of `tutor dev launch` / `tutor … init`, the same way every other Django app's migrations do - the backend appears in `INSTALLED_APPS` via its `lms.djangoapp` entry point, so the standard `migrate` step in `init` picks it up. No `CLI_DO_INIT_TASKS` hook is required. |
| **Frontend** | *(requires `tutor-mfe`)* Registers `DemographicsFields` against the `org.openedx.frontend.authn.register.additional_fields.v1` slot via `PLUGIN_SLOTS.add_item`. The component itself is resolved at MFE-build time by `frontend-app-authn`'s `module.config.js` `localModules` alias (workshop branch), which points at this repo's `frontend/` directory. See [`frontend/README.md`](../frontend/README.md) for the full mechanism. If `tutor-mfe` is not installed the backend half still works - the plugin degrades gracefully. |

The frontend slot is empty by default (no built-in widget to replace), so the plugin uses a plain `PLUGIN_OPERATIONS.Insert`. Compare with `tutor-contrib-sample-plugin`, which uses `Hide` + `Insert` because it replaces an existing default widget.

---

## Requirements

- **Tutor** - `main` branch (pinned in [`pyproject.toml`](./pyproject.toml) as `tutor @ git+https://github.com/overhangio/tutor.git@main`)
- **tutor-mfe** - `main` branch (also pinned in `pyproject.toml`); optional in principle, but installed by default because the workshop demonstrates the frontend slot

Both are installed automatically by `pip install -e ./tutor_plugin`.

---

## Installation

### Install the Tutor plugin package

```bash
# From this repository (development / workshop)
pip install -e .
```

This pulls in `tutor @ main` and `tutor-mfe @ main` as declared dependencies, so you do **not** need to install Tutor separately.

### Enable the plugin

```bash
tutor plugins enable demographics_plugin
tutor plugins enable mfe
tutor plugins list   # both should appear as enabled
```

---

## Development Setup

This is the supported workflow today. It relies on sibling checkouts of three workshop-branch repos being mounted alongside this plugin's `backend/` directory.

### 1. Mount the backend source

```bash
# From the repo root — maps ./backend into the openedx container's virtualenv
tutor mounts add ./backend
tutor mounts list   # should show: openedx <= .../backend
```

The `MOUNTED_DIRECTORIES.add_item(("openedx", "backend"))` line in `plugin.py` makes this work; without it the mount would be ignored.

### 2. Mount the workshop branches of the upstream repos

```bash
tutor mounts add ../openedx-platform
tutor mounts add ../frontend-app-authn
tutor mounts add ../openedx-events
```

`frontend-app-authn` in particular is what supplies the active `env.config.jsx` and the `module.config.js` `localModules` alias that resolves `@openedx/openedx-demographics-plugin` to this repo's `frontend/` directory.

### 3. Launch (or restart) the dev environment

```bash
tutor dev launch
# or, if already running:
tutor dev stop && tutor dev start
```

Migrations for `registration_demographics` run automatically during `launch` / `init`, alongside every other Django app's migrations.

### 4. Verify the backend

```bash
tutor dev exec lms ./manage.py lms shell -c "
from registration_demographics.models import LearnerDemographics
print('Model loaded OK, table exists:', LearnerDemographics.objects.count() >= 0)
"
```

### 5. Verify the frontend slot (requires tutor-mfe)

Navigate to the registration page in your browser. The **Pronouns** text field and **Department** select should appear just above the Create Account button.

If the fields are missing, check the browser console for a `ReferenceError: DemographicsFields is not defined` - that usually means the mounted `frontend-app-authn` is not on the workshop branch (so its `env.config.jsx` doesn't import the component). Confirm with:

```bash
tutor dev exec authn cat /openedx/app/env.config.jsx | grep DemographicsFields
```

---

## Production Setup (aspirational)

> **Not currently tested end-to-end.** The pieces are in place in `plugin.py` but the relevant patches are commented out because the workshop runs entirely off mounted sources. The notes below describe how to switch the plugin from "mounted source" mode to "self-contained image" mode.

The production path replaces each of the three dev mounts with a build-time install patch:

| Dev mount (current default) | Production replacement (commented out in `plugin.py`) |
|-----------------------------|--------------------------------------------------------|
| `tutor mounts add ./backend` | `openedx-lms-dockerfile-post-python-requirements` patch that `pip install`s `openedx-registration-demographics-plugin` into the LMS image. Once installed this way, Django sees the app via its `lms.djangoapp` entry point and `tutor … init` runs its migrations along with everything else - no special CLI hook is required. |
| `tutor mounts add ../frontend-app-authn` (workshop branch) | `mfe-dockerfile-post-npm-install` patch that `npm install`s `@openedx/openedx-demographics-plugin` into every MFE image, plus the `mfe-env-config-buildtime-imports` patch that injects `import { DemographicsFields } from '@openedx/openedx-demographics-plugin';` into the generated `env.config.jsx`. The `PLUGIN_SLOTS.add_item(...)` call (already active) then registers the widget at runtime. |
| `tutor mounts add ../openedx-events` / `tutor mounts add ../openedx-platform` | Once the workshop branches are merged upstream, the corresponding releases of `openedx-events` and `edx-platform` carry the new signal and the filter/event firing site natively - no patch needed. |

### Enabling the production patches

1. Publish `openedx-registration-demographics-plugin` to PyPI and `@openedx/openedx-demographics-plugin` to npm.
2. In `tutordemographicsplugin/plugin.py`, uncomment:
   - the `openedx-lms-dockerfile-post-python-requirements` block,
   - the `mfe-dockerfile-post-npm-install` block,
   - the `mfe-env-config-buildtime-imports` block.
3. Remove the corresponding `tutor mounts add` lines from your provisioning scripts.
4. Build images and deploy:

   ```bash
   tutor images build openedx   # LMS image with backend plugin
   tutor images build mfe       # MFE images with frontend plugin
   tutor local launch
   ```

5. Verify:

   ```bash
   # Backend - confirm migrations ran
   tutor local exec lms ./manage.py lms showmigrations registration_demographics

   # REST API - should return 200 with an empty demographics record for the user
   curl -H "Authorization: Bearer <jwt>" \
     https://<your-lms-domain>/api/registration-demographics/v1/me/
   ```

---

## Configuration

### Customising the department list (backend)

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

### Customising the department list (frontend)

The `DemographicsFields` component accepts a `departments` prop (array of `{value, label}` objects). The current `PLUGIN_SLOTS.add_item` call in `plugin.py` does **not** pass `pluginProps`, so the component falls back to its built-in default list. To override, edit the slot registration in `plugin.py` to pass `pluginProps`:

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

### Backend plugin not found in LMS (dev mounts)

```bash
# Confirm the mount is registered
tutor mounts list | grep backend

# Confirm the package is importable inside the container
tutor dev exec lms python -c "import registration_demographics; print(registration_demographics.__file__)"
```

If the import fails, the mount is registered but the editable install didn't take - rebuild the openedx dev image (`tutor images build openedx-dev`) and restart.

### Frontend fields not appearing

1. Confirm `tutor-mfe` is installed and enabled: `tutor plugins list | grep mfe`.
2. Confirm the mounted `frontend-app-authn` is on the workshop branch:
   ```bash
   git -C ../frontend-app-authn rev-parse --abbrev-ref HEAD
   # expected: bmtcril/oex26_conference_workshop
   ```
3. Confirm `env.config.jsx` in the running `authn` MFE imports the component:
   ```bash
   tutor dev exec authn cat /openedx/app/env.config.jsx | grep DemographicsFields
   ```
4. If you're on the production path instead, rebuild the MFE image after enabling the patches:
   ```bash
   tutor images build mfe
   tutor dev restart mfe
   ```

### Migrations not applied

```bash
tutor dev run lms ./manage.py lms showmigrations registration_demographics
# If 0001_initial shows [ ]:
tutor dev run lms ./manage.py lms migrate registration_demographics
```

In a healthy setup this should never be necessary - `tutor … init` runs `migrate` for every installed Django app, including this one.

### Department validation errors at registration

The `department` value submitted by the frontend must exactly match one of the strings in `REGISTRATION_DEMOGRAPHICS_DEPARTMENTS`. Check the setting is applied in the running container:

```bash
tutor dev exec lms ./manage.py lms shell -c "
from django.conf import settings
print(getattr(settings, 'REGISTRATION_DEMOGRAPHICS_DEPARTMENTS', 'NOT SET'))
"
```
