# Open edX Registration Demographics Plugin

> **Workshop reference implementation for [OEX 2026 — Leveraging Open edX Extension Points](./workshop-plan.md).**
>
> Install one Tutor plugin, get an end-to-end demographics-collection feature
> across MFE, filters, events, and a Django app.

This repository is the "finished state" companion to the OEX 2026 workshop. It
demonstrates every layer of the Open edX extension-point stack by solving a
single, real problem: **collecting additional demographic information
(pronouns, department) during learner registration and persisting it through
a pluggable pipeline.**

The structure deliberately mirrors
[`openedx/sample-plugin`](https://github.com/openedx/sample-plugin) so that
participants can compare the two side-by-side.

---

## Table of Contents

- [What this repository demonstrates](#what-this-repository-demonstrates)
- [Plugin types & where to find them here](#plugin-types--where-to-find-them-here)
- [Quick start](#quick-start)
- [Repository structure](#repository-structure)
- [Workshop section ↔ code map](#workshop-section--code-map)
- [Upstream patches](#upstream-patches)
- [Further reading](#further-reading)

---

## What this repository demonstrates

| Layer | What we extend | Where it lives |
|-------|----------------|----------------|
| **Frontend MFE** | New plugin slot in the registration form, filled by a React component that collects pronouns + department. | [`frontend/`](./frontend/) and [`upstream-patches/frontend-app-authn.patch`](./upstream-patches/) |
| **Filter** | New pipeline step on `StudentRegistrationRequested` that validates the demographic fields. | [`backend/src/registration_demographics/pipeline.py`](./backend/) |
| **Event** | A brand-new `RegistrationDemographicsCaptured` event fired after successful registration. | [`upstream-patches/openedx-events.patch`](./upstream-patches/) (definition) and [`backend/src/registration_demographics/signals.py`](./backend/) (receiver) |
| **Django app plugin** | New `LearnerDemographics` model, REST API, admin, migrations. | [`backend/src/registration_demographics/`](./backend/) |
| **Tutor plugin** | One-shot installer that wires everything above into LMS + the `authn` MFE. | [`tutor_plugin/tutordemographicsplugin/plugin.py`](./tutor_plugin/) |

> Aspects / xAPI integration is **out of scope** for this workshop but
> mentioned in [§6 of the workshop plan](./workshop-plan.md) as the next step.

---

## Plugin types & where to find them here

This table mirrors the sample-plugin's "Plugin Types" table, mapped to *this*
repo so you can flip between them.

| Plugin Type | Sample-plugin equivalent | This repo |
|-------------|--------------------------|-----------|
| Django App Plugin | `backend/sample_plugin/` | `backend/src/registration_demographics/` |
| Open edX Events receiver | `signals.py` | `backend/src/registration_demographics/signals.py` |
| Open edX Filters pipeline step | `pipeline.py` | `backend/src/registration_demographics/pipeline.py` |
| Frontend MFE plugin | `frontend/src/plugin.jsx` | `frontend/src/DemographicsFields.jsx` |
| Tutor plugin | `tutor/tutorsampleplugin/plugin.py` | `tutor_plugin/tutordemographicsplugin/plugin.py` |
| Upstream platform changes | _(none — sample-plugin only consumes existing extension points)_ | `upstream-patches/` |

The last row is the headline difference: this workshop is about **creating
new extension points**, not just consuming them, so the patches against
`frontend-app-authn`, `openedx-events`, and `edx-platform` live alongside the
plugin.

---

## Quick start

> **Prerequisites:** A working [Tutor](https://docs.tutor.edly.io/) dev
> environment, with [`tutor-mfe`](https://github.com/overhangio/tutor-mfe)
> installed.
>
> **Note:** Until the [`upstream-patches/`](./upstream-patches/) are merged
> upstream, you'll need to apply them to your local `frontend-app-authn`,
> `openedx-events`, and `edx-platform` checkouts before the demo will be
> fully functional. Each patch file has a detailed commit message explaining
> what to apply and why. The plugin itself degrades gracefully if the upstream
> hooks aren't present — useful while reviewing.

```bash
# 1. Clone this repo
git clone https://github.com/openedx/oex26-demographics-plugin.git
cd oex26-demographics-plugin

# 2. Mount the backend so dev edits are live
tutor mounts add ./backend

# 3. Install + enable the Tutor plugin
tutor plugins install ./tutor_plugin
tutor plugins enable demographics_plugin

# 4. Build & launch
tutor dev launch
```

Verification:

- **Frontend:** Visit the registration form; you should see *Pronouns* and
  *Department* fields injected by the plugin.
- **Backend:** Register a new user, then check
  `http://local.openedx.io/admin/registration_demographics/learnerdemographics/`.
- **Filter:** Try registering with an unrecognised department; the filter
  should reject the request with a useful error message.
- **Event:** Tail the LMS logs (`tutor dev logs lms`) for the
  `RegistrationDemographicsCaptured` line emitted by the receiver.

---

## Repository structure

```text
oex26-demographics-plugin/
├── README.md                       ← you are here
├── workshop-plan.md                ← workshop facilitator plan
├── LICENSE                         ← Apache-2.0
├── backend/                        ← Django app plugin (pip-installable)
│   └── src/registration_demographics/
├── frontend/                       ← React component (npm-publishable)
│   └── src/DemographicsFields.jsx
├── tutor_plugin/                   ← Tutor plugin that ties it all together
│   └── tutordemographicsplugin/plugin.py
└── upstream-patches/               ← what we'd send upstream to make the
    ├── frontend-app-authn.patch    ←   extension points exist
    ├── openedx-events.patch
    └── edx-platform.patch
```

Each subdirectory has its own `README.md` with deeper dives.

---

## Workshop section ↔ code map

For facilitators walking through the [workshop plan](./workshop-plan.md):

| Workshop section | Files to open |
|------------------|---------------|
| §3 Anatomy of extension points | this README's table + the architecture diagram in `workshop-plan.md` |
| §4 Frontend: adding a plugin slot | `upstream-patches/frontend-app-authn.patch`, then `frontend/src/DemographicsFields.jsx` |
| §5A Adding a filter | `backend/src/registration_demographics/pipeline.py`, `backend/src/registration_demographics/settings/common.py` |
| §5B Adding / extending an event | `upstream-patches/openedx-events.patch`, `upstream-patches/edx-platform.patch`, `backend/src/registration_demographics/signals.py` |
| §6 Django plugins & Tutor wiring | `backend/pyproject.toml`, `backend/src/registration_demographics/apps.py`, `tutor_plugin/tutordemographicsplugin/plugin.py` |
| §7 Getting it merged | commit messages on each patch in `upstream-patches/` |

---

## Upstream patches

The patches in [`upstream-patches/`](./upstream-patches/) are written as if
they were ready-to-send PRs against:

- [`openedx/frontend-app-authn`](https://github.com/openedx/frontend-app-authn) — adds the new `PluginSlot`.
- [`openedx/openedx-events`](https://github.com/openedx/openedx-events) — defines `RegistrationDemographicsCaptured`.
- [`openedx/edx-platform`](https://github.com/openedx/edx-platform) — fires the new filter and event.

Their commit messages double as the "discussion-first" forum posts described
in workshop §7.

---

## End-to-end smoke test

See **[`E2E.md`](./E2E.md)** for the complete walkthrough — from applying the upstream patches to verifying the filter, event, DB record, and REST API in a `tutor dev` environment.

---

## Further reading

- [Open edX Hooks Extension Framework](https://docs.openedx.org/en/latest/developers/concepts/hooks_extension_framework.html)
- [`openedx-filters` reference](https://docs.openedx.org/projects/openedx-filters/en/latest/reference/filters.html)
- [`openedx-events` reference](https://docs.openedx.org/projects/openedx-events/en/latest/)
- [Frontend Plugin Framework](https://github.com/openedx/frontend-plugin-framework)
- [Tutor plugin development](https://docs.tutor.edly.io/tutorials/plugin.html)
- [`openedx/sample-plugin`](https://github.com/openedx/sample-plugin) — the consumer-side companion to this repo.
