# Open edX Registration Demographics Plugin

> Install one Tutor plugin, get an end-to-end demographics-collection feature
> across MFE, filters, events, and a Django app.

This repository is a reference implementation that demonstrates most layers of
the Open edX extension-point stack by solving a single, real problem:
**collecting additional demographic information during learner registration and persisting it through a pluggable pipeline.**

The structure deliberately mirrors
[`openedx/sample-plugin`](https://github.com/openedx/sample-plugin) so that
participants can compare the two side-by-side.

---

## Table of Contents

- [What this repository demonstrates](#what-this-repository-demonstrates)
- [Plugin types & where to find them here](#plugin-types--where-to-find-them-here)
- [Quick start](#quick-start)
- [Repository structure](#repository-structure)
- [Workshop branches](#workshop-branches)
- [End-to-end smoke test](#end-to-end-smoke-test)
- [Further reading](#further-reading)

---

## What this repository demonstrates

| Layer | What we extend | Where it lives |
|-------|----------------|----------------|
| **Frontend MFE** | New plugin slot in the registration form, filled by a React component that collects pronouns + department. | [`frontend/`](./frontend/) and [`frontend-app-authn` @ `bmtcril/oex26_conference_workshop`](https://github.com/openedx/frontend-app-authn/tree/bmtcril/oex26_conference_workshop) |
| **Filter** | New pipeline step on `StudentRegistrationRequested` that validates the demographic fields. | [`backend/src/registration_demographics/pipeline.py`](./backend/) |
| **Event** | A brand-new `RegistrationDemographicsCaptured` event fired after successful registration. | [`openedx-events` @ `bmtcril/oex26_conference_workshop`](https://github.com/openedx/openedx-events/tree/bmtcril/oex26_conference_workshop) (definition) and [`backend/src/registration_demographics/signals.py`](./backend/) (receiver) |
| **Django app plugin** | New `LearnerDemographics` model, REST API, admin, migrations. | [`backend/src/registration_demographics/`](./backend/) |
| **Tutor plugin** | One-shot installer that wires everything above into LMS + the `authn` MFE. | [`tutor_plugin/tutordemographicsplugin/plugin.py`](./tutor_plugin/) |

> Aspects / xAPI integration is **out of scope** for this workshop but
> mentioned as a next step.

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
| Upstream platform changes | _(none — sample-plugin only consumes existing extension points)_ | workshop branches (see below) |

The last row is the headline difference: this workshop is about **creating
new extension points**, not just consuming them, so the changes against
`frontend-app-authn`, `openedx-events`, and `openedx-platform` live in
dedicated workshop branches alongside the plugin.

---

## Quick start

> **Prerequisites:** A working [Tutor](https://docs.tutor.edly.io/) dev
> environment, with [`tutor-mfe`](https://github.com/overhangio/tutor-mfe)
> installed.
>
> **Note:** This demo requires the workshop branches of `frontend-app-authn`,
> `openedx-events`, and `openedx-platform` to be checked out as siblings of
> this repo. The automated setup script handles mounting and verification.

```bash
# 1. Clone this repo and the three workshop branches as siblings
git clone https://github.com/bmtcril/oex26-demographics-plugin.git
git clone --branch bmtcril/oex26_conference_workshop https://github.com/openedx/frontend-app-authn.git
git clone --branch bmtcril/oex26_conference_workshop https://github.com/openedx/openedx-events.git
git clone --branch bmtcril/oex26_conference_workshop https://github.com/openedx/openedx-platform.git

# 2. Run the automated setup (mounts all repos, installs plugins, launches)
cd oex26-demographics-plugin
bash scripts/setup_dev.sh
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
├── LICENSE                         ← Apache-2.0
├── scripts/
│   └── setup_dev.sh                ← automated dev environment setup
├── backend/                        ← Django app plugin (pip-installable)
│   └── src/registration_demographics/
├── frontend/                       ← React component (local build, no npm publish)
│   └── src/DemographicsFields.jsx
└── tutor_plugin/                   ← Tutor plugin that ties it all together
    └── tutordemographicsplugin/plugin.py
```

The upstream platform changes live in dedicated workshop branches:

| Repo | Branch |
|------|--------|
| [`openedx/frontend-app-authn`](https://github.com/openedx/frontend-app-authn/tree/bmtcril/oex26_conference_workshop) | `bmtcril/oex26_conference_workshop` |
| [`openedx/openedx-events`](https://github.com/openedx/openedx-events/tree/bmtcril/oex26_conference_workshop) | `bmtcril/oex26_conference_workshop` |
| [`openedx/openedx-platform`](https://github.com/openedx/openedx-platform/tree/bmtcril/oex26_conference_workshop) | `bmtcril/oex26_conference_workshop` |

Each subdirectory has its own `README.md` with deeper dives.

---

## Workshop branches

The upstream platform changes are staged in dedicated branches, written as if
they were ready-to-send PRs:

- [`openedx/frontend-app-authn` @ `bmtcril/oex26_conference_workshop`](https://github.com/openedx/frontend-app-authn/tree/bmtcril/oex26_conference_workshop) — adds the new `PluginSlot`.
- [`openedx/openedx-events` @ `bmtcril/oex26_conference_workshop`](https://github.com/openedx/openedx-events/tree/bmtcril/oex26_conference_workshop) — defines `RegistrationDemographicsCaptured`.
- [`openedx/openedx-platform` @ `bmtcril/oex26_conference_workshop`](https://github.com/openedx/openedx-platform/tree/bmtcril/oex26_conference_workshop) — fires the new filter and event.

Their commit messages double as the "discussion-first" forum posts.

---

## End-to-end smoke test

See **[`E2E.md`](./E2E.md)** for the complete walkthrough — from checking out the workshop branches to verifying the filter, event, DB record, and REST API in a `tutor dev` environment.

---

## Further reading

- [Open edX Hooks Extension Framework](https://docs.openedx.org/en/latest/developers/concepts/hooks_extension_framework.html)
- [`openedx-filters` reference](https://docs.openedx.org/projects/openedx-filters/en/latest/reference/filters.html)
- [`openedx-events` reference](https://docs.openedx.org/projects/openedx-events/en/latest/)
- [Frontend Plugin Framework](https://github.com/openedx/frontend-plugin-framework)
- [Tutor plugin development](https://docs.tutor.edly.io/tutorials/plugin.html)
- [`openedx/sample-plugin`](https://github.com/openedx/sample-plugin) — the consumer-side companion to this repo.
