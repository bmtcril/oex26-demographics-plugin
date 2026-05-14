# Leveraging Open edX Extension Points

## OEX 2026 Conference Workshop Plan

### Blurb

> Sometimes the extension point you need just isn't there yet – it's time to make it! We'll walk you through it all: what makes a strong extension point, the nuts and bolts of creating one, and getting it merged upstream so the whole community can benefit.
>
> Participants will learn how to modify an MFE to add a new frontend plugin slot, how to add a new event or filter, and when to leverage Tutor plugins, plus how to determine where the core needs to be modified to achieve goals. Meet with leaders from the Open edX working groups, and determine where to seek assistance and advice before making an upstream pull request.
>
> This workshop is aimed at software developers who have familiarity with the Open edX software; comfort with Python and/or JavaScript will be useful for the hands-on portion.

---

## Workshop Goals

By the end of this workshop, participants will be able to:

1. **Identify** where an extension point should live (frontend slot, filter, event, Django plugin, Tutor plugin).
2. **Implement** a new frontend plugin slot in an MFE.
3. **Implement** a new `openedx-filters` filter and `openedx-events` event on the backend.
4. **Wire up** a Django plugin to consume these extension points (new models, new data).
5. **Navigate the contribution process** — know who to talk to, where to propose changes, and how to get an upstream PR accepted.

---

## Schedule (2 hours total)

| Time        | Duration | Section                                                    |
|-------------|----------|------------------------------------------------------------|
| 0:00–0:05   | 5 min    | **Welcome & orientation** — goals, prerequisites, handouts |
| 0:05–0:15   | 10 min   | **Why extension points?** — philosophy & when to extend    |
| 0:15–0:25   | 10 min   | **Anatomy of extension points** — the four layers          |
| 0:25–0:35   | 10 min   | **Frontend: adding a plugin slot** — walkthrough           |
| 0:35–1:05   | 30 min   | **Backend: filters, events & Django plugin** — live coding walkthrough |
| 1:05–1:10   | 5 min    | **Break**                                                  |
| 1:10–1:20   | 10 min   | **Tutor wiring** — bringing it all together                |
| 1:20–1:25   | 5 min    | **Getting it merged** — contribution process & contacts    |
| 1:25–1:40   | 15 min   | **Brainstorm session** — groups identify their own extension points |
| 1:40–2:00   | 20 min   | **Implementation lab** — hands-on time with facilitator help |

---

## Repository State

The running example lives in this repo. As facilitators, this is what's already wired up vs. what still needs work before the workshop:

| Section | Code artefact                                                                                | Status |
|---------|----------------------------------------------------------------------------------------------|--------|
| §4      | [`frontend-app-authn` @ `bmtcril/oex26_conference_workshop`](https://github.com/openedx/frontend-app-authn/tree/bmtcril/oex26_conference_workshop) — adds the slot + `slot.md` doc | ✅ |
| §4      | `frontend/` — npm package providing the `DemographicsFields` plugin component (local build, no publish) | ✅ |
| §5A     | `backend/src/registration_demographics/pipeline.py` — `ValidateDemographicsFields` step      | ✅ |
| §5A     | `backend/src/registration_demographics/settings/common.py` — filter pipeline registration    | ✅ |
| §5B     | `backend/src/registration_demographics/events.py` — `REGISTRATION_DEMOGRAPHICS_CAPTURED`     | ✅ |
| §5B     | `backend/src/registration_demographics/signals.py` — idempotent receiver                     | ✅ |
| §5B     | [`openedx-events` @ `bmtcril/oex26_conference_workshop`](https://github.com/openedx/openedx-events/tree/bmtcril/oex26_conference_workshop) — upstream signal definition | ✅ |
| §5B     | [`openedx-platform` @ `bmtcril/oex26_conference_workshop`](https://github.com/openedx/openedx-platform/tree/bmtcril/oex26_conference_workshop) — fires the signal from the LMS register view | ✅ |
| §6      | `backend/src/registration_demographics/apps.py` — Django plugin entry point                  | ✅ |
| §6      | `backend/src/registration_demographics/{models,serializers,views,urls}.py` + migration       | ✅ |
| §6      | `backend/tests/` — model, viewset, pipeline, signal, smoke tests                             | ✅ |
| §6      | `tutor_plugin/tutordemographicsplugin/plugin.py` — Tutor plugin                              | ✅ |
| —       | Top-level `README.md` (Quick Start, plugin types table, workshop ↔ code map)                 | ✅ |
| —       | `E2E.md` — end-to-end smoke test commands                                                     | ✅ |

The `private/Demographic Plumbing Plugin Repository Architecture Plan.md` document captures the full build plan and the renumbered step ordering we're following.

---

## Narrative Arc & Running Example

### The story: "Additional Registration Demographics"

The entire workshop is threaded through a single, realistic use case:

> **An institution wants to collect additional demographic information during learner registration** (e.g., preferred pronouns, department affiliation). The data should be stored in a pluggable way, displayed in the registration form via a frontend plugin slot, validated and persisted via a backend filter and event, and ultimately reportable through Aspects.

This use case is compelling because:

- Custom registration fields are **not yet supported** in the MFE port ([MFE Rewrite Tracker](https://openedx.atlassian.net/wiki/spaces/COMM/pages/4262363137/MFE+Rewrite+Tracker)).
- It touches every layer of the extension-point stack (frontend slot → filter → event → Django model → Aspects).
- It is a real pain point that many community operators share.
- It demonstrates why **creating extension points is better than maintaining a fork**.

---

## Section Details

### 1. Welcome & Orientation (5 min)

- Introduce facilitators and their working-group affiliations.
- Distribute handouts (with QR links to documentation — see [Handouts](#handouts) section below) and connection info papers (SSH credentials and URLs for pre-built cloud servers).
- Confirm participants can SSH into their assigned cloud server — no local Tutor setup required.
- Set expectations: "We will build a working feature together, end-to-end."

### 2. Why Extension Points? (10 min)

**Key message:** *It is in your best interest to create extension points instead of maintaining a fork.*

Cover briefly:

- **The cost of forking** — merge conflicts every release, diverging codebase, isolation from community improvements.
- **The extension-point philosophy** — push complexity into the plugin; keep the platform thin and maintainable.
- **Decision framework: "Where does my extension point go?"**

  | I need to…                                    | Extension mechanism              |
  |-----------------------------------------------|----------------------------------|
  | Add or modify UI in an MFE                    | **Frontend plugin slot**         |
  | Intercept / modify a backend process in-flight| **`openedx-filters`**            |
  | React to something that happened              | **`openedx-events`**             |
  | Emit data to external systems                 | **Event bus → message broker**   |
  | Store new data, add new APIs                  | **Django plugin (entry points)** |
  | Customize Tutor build/config                  | **Tutor plugin**                 |
  | Report on data in dashboards                  | **Aspects / xAPI extensions**    |

- Briefly mention external-integration paths (message bus, tracking events, xAPI) but note these are out of scope for hands-on today.

### 3. Anatomy of Extension Points — The Four Layers (10 min)

Walk through the architecture diagram (whiteboard or slide):

```
┌───────────────────────────────────────────┐
│  Frontend (MFE)                           │
│  ┌─────────────────────────────────────┐  │
│  │  Plugin Slot: <AdditionalRegInfo /> │  │
│  └─────────────────────────────────────┘  │
│               ▼ API call                  │
├───────────────────────────────────────────┤
│  Platform Extension Points                │
│  ┌────────────────┐  ┌─────────────────┐  │
│  │ openedx-filter │  │ openedx-event   │  │
│  │ (validate &    │  │ (emit after     │  │
│  │  transform)    │  │  registration)  │  │
│  └────────────────┘  └─────────────────┘  │
│               ▼ Django plugin             │
├───────────────────────────────────────────┤
│  Plugin (pip-installable Django app)      │
│  ┌─────────────────────────────────────┐  │
│  │ Models, receivers, API endpoints    │  │
│  └─────────────────────────────────────┘  │
│               ▼ event bus / tracking      │
├───────────────────────────────────────────┤
│  Reporting (Aspects, etc.)                │
│  Tracking, xAPI statements, dashboards    │
└───────────────────────────────────────────┘
```

- Explain how each layer is independently pluggable.
- Preview the files/repos we will touch.

### 4. Frontend: Adding a Plugin Slot (10 min)

> **Goal:** Add a `<PluginSlot>` to the registration form MFE that allows a plugin to inject additional form fields.

**Note for facilitators:** This is the third conference iterating on this material — keep frontend plugin instruction to ~10 minutes and point participants to documentation for deeper dives.

#### Live walkthrough

1. **Identify the insertion point** in the registration MFE.
   - Show the current registration form component.
   - Reference the old, non-implemented configurable registration approach: [ConfigurableRegistrationForm.jsx (line 14)](https://github.com/openedx/frontend-app-authn/blob/604a78500714d6a970855424a8f3b2e281b8c47e/src/register/components/ConfigurableRegistrationForm.jsx#L14).
   - Discuss: *When do you add to an existing MFE vs. create a new one?* (Rule of thumb: extend an existing MFE if the feature is logically co-located; create a new MFE only for a fully distinct domain.)

2. **Add the slot:**
   - Import `PluginSlot` from `@openedx/frontend-plugin-framework`.
   - Define a named slot — we use `org.openedx.frontend.authn.register.additional_fields.v1` (reverse-DNS, versioned). Walk through the naming convention; this is the form upstream reviewers will expect.
   - Place it in the JSX tree just above the submit button so plugins append fields rather than reorder the form's required ones.
   - Pass `formFields` and the form's change handler as `pluginProps` so the plugin component participates in the form's state machinery rather than maintaining shadow state.
   - Show the [`frontend-app-authn` workshop branch](https://github.com/openedx/frontend-app-authn/tree/bmtcril/oex26_conference_workshop) as the live reference: the diff against `RegistrationPage.jsx` plus the companion `RegisterAdditionalFieldsSlot/README.md` (the slot doc the Frontend WG expects on every new slot).

3. **Demonstrate the demographics plugin** rendering `pronouns` and `department` fields into the slot via the `frontend/` package's `DemographicsFields` component.
   - Show how a Tutor plugin injects the MFE plugin config so the slot is populated (forward-reference §6).

4. **Point to documentation** — QR code on handout for frontend plugin framework docs.

#### Key decisions to highlight

- React Query makes it easier to plug into existing API calls from a plugin (e.g., pulling extra data into the registration context).
- Prefer pushing complexity into the plugin over complicating the platform.

### 5. Backend: Filters, Events & Django Plugin (30 min)

> **Goal:** Add a new `openedx-filters` filter to the registration flow, extend an `openedx-events` event with demographic data, and wire it all into a pip-installable Django plugin.

This is the meatiest section and follows a live-coding format.

#### Part A: Adding a filter (10 min)

**Context:** Filters allow plugins to intercept and modify data mid-process. The existing [`StudentRegistrationRequested`](https://docs.openedx.org/projects/openedx-filters/en/latest/reference/filters.html#openedx_filters.learning.filters.StudentRegistrationRequested) filter is our model.

1. **Examine the existing filter** — show how `StudentRegistrationRequested` is defined and where it's called in registration code.
2. **Define a new filter** (or extend the existing one) that passes additional demographic fields through for validation/transformation.
   - Define the filter class in `openedx-filters`.
   - Add the filter pipeline call in `openedx-platform` registration code.
3. **Write a plugin receiver** in our demo Django plugin that hooks into the filter to validate the new fields (e.g., ensure "department" is a valid choice).

**Trivial warm-up example:** Before diving into demographics, optionally show a dead-simple filter — e.g., one that injects the current server time into a response — to make the mechanics clear without domain complexity.

**Talking point — filters are composable building blocks.** The demographics plugin's filter step reuses the *same* `validate_department` function as its DRF serializer. One source of truth produces a 400 in the REST flow and a `PreventRegistration` in the filter flow — different exception types for different transports, identical validation logic. Highlight this pattern so participants take away "filters compose with the rest of your Django app, they aren't a parallel universe."

**Talking point — merge, don't replace, in `OPEN_EDX_FILTERS_CONFIG`.** When a plugin's `plugin_settings()` registers a filter step, it must *append* to any existing pipeline for that filter type rather than overwriting it. Other plugins or the operator's Tutor config may already have steps registered on the same filter; clobbering them would be a silent and very nasty bug. Show `backend/src/registration_demographics/settings/common.py` as the canonical pattern: read the existing config, append our step if it isn't already there, and write back.

#### Part B: Defining a new event (10 min)

**Context:** Events are fired *after* something has happened and allow asynchronous reactions.

1. **Show the existing registration event** (`STUDENT_REGISTRATION_COMPLETED`) and its `UserData`-only payload.
2. **Decide: extend the existing event vs. define a new one?** Walk through the trade-off and land on **defining a new event** for the running example. The reasons (worth saying out loud — they're the reasons reviewers will ask about):
   - Extending `STUDENT_REGISTRATION_COMPLETED` would force every existing receiver to deal with new attrs and would couple a generic event to one specific use case.
   - A dedicated `REGISTRATION_DEMOGRAPHICS_CAPTURED` lets deployments that don't collect demographics ignore it entirely, and lets deployments that *do* route it onto the event bus without touching the higher-volume registration-completed stream.
   - Versioning the new signal independently (`...captured.v1`) means future field-shape changes don't bump the older event.
3. **Define the event** in `backend/src/registration_demographics/events.py` — `RegistrationDemographicsData` (attrs class) + the `OpenEdxPublicSignal`. Frame this as the *staging ground* pattern (see §7 talking point): the definition lives in the plugin while the upstream PR is in flight.
4. **Write an event receiver** in `backend/src/registration_demographics/signals.py` that persists the demographic data via `update_or_create` (idempotent — see talking point below).
5. **Show the upstream branches** ([`openedx-events`](https://github.com/openedx/openedx-events/tree/bmtcril/oex26_conference_workshop), [`openedx-platform`](https://github.com/openedx/openedx-platform/tree/bmtcril/oex26_conference_workshop)) as the eventual destination: define the signal in `openedx-events.learning`, fire it from the LMS register view. The plugin's local `events.py` keeps the same `event_type` string so receivers don't break when the import path migrates.
6. **Briefly mention** the event bus (Kafka/Redis) as a mechanism for pushing events to external systems — out of scope for hands-on today.

**Talking point — filter vs. event, division of labour.** Show the demographics plugin's two halves side-by-side: the *filter* (`pipeline.py`) gates registration and validates input — it raises `PreventRegistration` and aborts. The *event* receiver (`signals.py`) records the fact that registration happened — it logs and recovers, never raising. Same domain, different transport, different failure semantics. The pithy version: "filters say *no*; events say *FYI*." Use this to help participants pick the right tool when they design their own extension points in §8.

**Talking point — design receivers to be idempotent from day one.** The demographics receiver uses `update_or_create` rather than `create`, even though today the event fires exactly once per registration. The reason is forward-compatibility: once the event bus is wired up, exactly-once delivery is hard, and idempotent receivers turn event-bus migration into a no-code change for downstream consumers. Show `signals.py` as the pattern.

#### Part C: Django plugin structure (10 min)

**Context:** The filter and event receivers we just wrote need a home — a pip-installable Django app that the platform loads via entry points.

1. **Walk through `backend/`:**
   - `pyproject.toml` entry point — `lms.djangoapp` only. Worth saying *why*: registration is LMS-side, the demographics REST API is consumed by the authn MFE, and there's no Studio surface. Compare with `sample-plugin` which registers under both `lms.djangoapp` and `cms.djangoapp` because its course-archive feature is meaningful in both. **The right entry-point set is a design decision, not boilerplate.**
   - Settings-based plugin registration via `apps.py`'s `plugin_app = {...}` and `settings/{common,production,test}.py`.
   - Adding new models, migrations, and API endpoints — point to `models.py`, `views.py`, `serializers.py`, `urls.py`, and the committed migration.
   - Connecting filter/event receivers via `AppConfig.ready()` importing `signals` and `pipeline`.

   **Key principle: inherit, don't override.** A plugin should generally
   *inherit* the platform's `REST_FRAMEWORK` defaults (JWT, OAuth2, session
   auth), `MIDDLEWARE`, logging config, etc. — only override at the
   view/setting level when the plugin genuinely needs different behaviour
   for one endpoint. Overriding `authentication_classes` on a viewset, for
   example, breaks every deployment that has tuned its auth backends.
   Show the demographics view as a positive example: it sets
   `permission_classes` (intentional, plugin-specific) but leaves auth
   to the platform.

### 6. Tutor Wiring (10 min)

> **Goal:** Show how the Django plugin (and the frontend component) get installed and configured via a Tutor plugin.

1. **Tutor integration** (walk through `tutor/tutordemographicsplugin/plugin.py`):
   - `MOUNTED_DIRECTORIES.add_item(("openedx", "backend"))` so `tutor mounts add ./backend` works for dev.
   - `ENV_PATCHES["openedx-lms-dockerfile-post-python-requirements"]` — installs the plugin package into the LMS image only (not CMS, consistent with the `lms.djangoapp`-only entry point).
   - `CLI_DO_INIT_TASKS` — runs `./manage.py lms migrate registration_demographics` on init.
   - `tutormfe`-conditional patches: `mfe-dockerfile-post-npm-install` to build and install the frontend package locally (via `npm install` with a local path — no npm registry publish required), `mfe-env-config-buildtime-imports` to import `DemographicsFields`, and `PLUGIN_SLOTS.add_item(...)` to register it against `org.openedx.frontend.authn.register.additional_fields.v1`. The plugin degrades gracefully if `tutormfe` isn't installed.
   - Run through `tutor plugins install ./tutor` → `tutor plugins enable demographics_plugin` → `tutor dev launch`.

   **Talking point — LMS-only patch mirrors the LMS-only entry point.** The plugin uses `openedx-lms-dockerfile-post-python-requirements` rather than the shared `openedx-dockerfile-post-python-requirements`. This is the same scope decision made in `pyproject.toml` (`lms.djangoapp` only) now showing up again in the Tutor layer — the two reinforce each other. Ask participants: *what would break if we used the shared patch but kept the LMS-only entry point?* Answer: nothing at runtime, but CMS images would carry a package they never load, which wastes image size and creates a maintenance surface. The layers should stay consistent.

   **Talking point — graceful degradation with `try/except ImportError`.** The `_tutormfe_available` guard at the top of `plugin.py` means the backend half of the plugin (filter, event, model, API) works on any deployment, even one that hasn't migrated to MFEs. Operators who are still on the legacy registration page simply don't get the frontend fields — they can collect demographics via the REST API by other means. This pattern is worth generalising: always ask "what does my plugin do if its optional dependencies aren't present?" and design the guard before writing the conditional code.

   **Talking point — three steps to wire a frontend plugin, and why each is necessary.**
   - *Step 1 (`mfe-dockerfile-post-npm-install`)* — builds the local npm package and installs it into the MFE Docker image at build time (using a local path, as a developer would). Without this the import in step 2 fails at container start.
   - *Step 2 (`mfe-env-config-buildtime-imports`)* — adds the `import` statement to `env.config.jsx`. The plugin slot config in step 3 references `DemographicsFields` by name; it must be in scope in that file or the MFE throws a ReferenceError.
   - *Step 3 (`PLUGIN_SLOTS.add_item(...)`)* — registers the component against the slot ID at runtime. Steps 1 and 2 together just make the code available; this step actually connects it to the UI.
   The order matters and each step is load-bearing. A common mistake is to do step 3 and forget step 1 or 2, which produces a confusing ReferenceError with no obvious link to the missing install.

   **Talking point — Insert without Hide.** The sample-plugin's learner-dashboard slot uses `PLUGIN_OPERATIONS.Hide` to remove the default widget before inserting its own replacement. Our slot (`additional_fields`) is *empty by default* — there is no built-in widget to hide. Using a bare `Insert` here is intentional, not an omission. Ask participants to spot the difference when reading sample-plugin's plugin.py alongside ours.

3. **Pushing to Aspects (mention only):**
   - Events emitted to the event bus can be consumed by Aspects pipelines.
   - Custom xAPI statement extensions can carry the demographic data into reporting dashboards.
   - This is a "next step" for participants to explore.

### 7. Getting It Merged (5 min)

**Key message:** *Know who to talk to before you write the code.*

- **Step 1: Discuss first.** Post in the [Open edX discussion forums](https://discuss.openedx.org/) or the relevant working group's Slack channel.
- **Step 2: Create a proposal.** For significant extension points, write a lightweight proposal (even a forum post) describing the use case and proposed API surface.
- **Step 3: Find your reviewers.** Identify the relevant working group:
  - **Build-Test-Release (BTR)** — for release process and Tutor questions.
  - **Frontend Working Group** — for MFE plugin slots and frontend architecture.
  - **Data Working Group** — for events, Aspects, xAPI.
  - Check the [CODEOWNERS](https://github.com/openedx/edx-platform/blob/master/.github/CODEOWNERS) file in the repo you're modifying.
- **Step 4: Open a PR** with tests, documentation, and an ADR if the change warrants it.
- **Step 5: Be responsive.** Reviews go faster when you respond to feedback promptly.

**Talking point — the "staging ground" pattern for new extension points.** Defining a brand-new event or filter upstream first, then writing a plugin against it, is a common rookie mistake — you end up with a half-designed API blocked on review. The pragmatic path is the opposite: define the event/filter *inside your plugin* (see `backend/src/registration_demographics/events.py`), get a receiver and tests working, run it in production for a release or two, then propose moving the *stabilised* definition upstream. Pin the `event_type` / `filter_type` string from day one so receivers don't break when the import path changes. The workshop branches show what those eventual upstream PRs look like, with commit messages written *as* the PR descriptions:

- [`openedx-events` @ `bmtcril/oex26_conference_workshop`](https://github.com/openedx/openedx-events/tree/bmtcril/oex26_conference_workshop) — defines `RegistrationDemographicsData` + `REGISTRATION_DEMOGRAPHICS_CAPTURED` in `openedx_events.learning`. Note the commit message argues for a *new* event vs. extending an existing one — that argument is the PR.
- [`openedx-platform` @ `bmtcril/oex26_conference_workshop`](https://github.com/openedx/openedx-platform/tree/bmtcril/oex26_conference_workshop) — fires the new signal from the LMS `create_account_with_params` view. Note the explicit choice to read from `request.POST` rather than the Django form (a deployment-optionality argument).
- [`frontend-app-authn` @ `bmtcril/oex26_conference_workshop`](https://github.com/openedx/frontend-app-authn/tree/bmtcril/oex26_conference_workshop) — adds the slot to `RegistrationPage`, plus the `slot.md` doc the Frontend WG expects on every new slot.

These are the artefacts you'd send upstream once the plugin has soaked in production. **They're also the artefacts to read *before* writing the plugin** — the commit messages are a working template for writing your own upstream PR descriptions.

Emphasize:
- The community *wants* more extension points — you're doing everyone a favor.
- Extension points reduce maintenance burden for the whole ecosystem.
- Start small, iterate, and communicate.

### 8. Brainstorm Session (15 min)

Break participants into groups of 3–5. Each group should:

1. **Identify a real extension point** they wish existed (or that they've been working around with a fork).
2. **Classify it** using the decision framework from Section 2 (frontend slot? filter? event? Django plugin?).
3. **Sketch the API surface** — what data flows in/out? Where does it hook in?
4. **Identify the repos** that would need to change.
5. **Prepare a 60-second pitch** for the room.

Facilitators circulate to coach and suggest approaches.

After 10 minutes, each group gives their 60-second pitch. Facilitators provide brief feedback and point to relevant prior art or contacts.

### 9. Implementation Lab (30 min)

Participants work on either:

- **Option A:** Finish the running example from the walkthrough sections — get the full demographics flow working in their Tutor dev environment.
- **Option B:** Start implementing the extension point their group brainstormed in Section 8.

Facilitators roam the room to help with:
- Environment issues (Tutor, Docker, etc.).
- Code questions (filter/event definitions, slot configuration).
- Contribution process questions (where to propose, who to tag).

---

## Handouts

Prepare a one-page (front-and-back) handout with QR codes linking to:

| Resource | URL |
|----------|-----|
| Frontend Plugin Framework docs | _TBD — link to `@openedx/frontend-plugin-framework` README or docs_ |
| `openedx-filters` reference | https://docs.openedx.org/projects/openedx-filters/en/latest/reference/filters.html |
| `openedx-events` reference | https://docs.openedx.org/projects/openedx-events/en/latest/ |
| MFE Rewrite Tracker | https://openedx.atlassian.net/wiki/spaces/COMM/pages/4262363137/MFE+Rewrite+Tracker |
| Open edX Contributing Guide | https://docs.openedx.org/en/latest/developers/references/developer_guide/process/contributor.html |
| Open edX Discussion Forums | https://discuss.openedx.org/ |
| Tutor Plugin Tutorial | https://docs.tutor.edly.io/tutorials/plugin.html |
| This workshop's repository | _TBD — GitHub link to sample code_ |

The handout should also include:

- The architecture diagram from Section 3.
- The "decision framework" table from Section 2.
- A quick-reference for the key commands (`tutor plugins enable`, `tutor dev run`, etc.).

---

## Pre-Workshop Preparation

### For facilitators

- [x] Backend Django plugin built (`backend/`): model + migration, REST API, filter pipeline step, event + receiver, settings wiring, tests.
- [x] Upstream branches prepared: [`openedx-events`](https://github.com/openedx/openedx-events/tree/bmtcril/oex26_conference_workshop), [`openedx-platform`](https://github.com/openedx/openedx-platform/tree/bmtcril/oex26_conference_workshop), [`frontend-app-authn`](https://github.com/openedx/frontend-app-authn/tree/bmtcril/oex26_conference_workshop).
- [ ] Frontend npm package (`frontend/`) — `DemographicsFields` plugin component + `package.json`; use local build (no npm publish).
- [ ] Tutor plugin (`tutor/tutordemographicsplugin/plugin.py`) — mounts, env patches, init tasks, MFE slot wiring via local npm install.
- [ ] Top-level `README.md` and `docs/E2E.md` (or README section) with the end-to-end smoke-test commands.
- [ ] Provision and test cloud servers; prepare connection info papers (one per participant with SSH credentials and URLs).
- [ ] Test the full flow end-to-end on the cloud servers using the workshop branches.
- [ ] Prepare slides for Sections 2 and 3 (can be minimal — diagrams and bullet points).
- [ ] Print handouts and connection info papers.
- [ ] Coordinate with working group leads who will be present for the brainstorm and lab portions.

### For participants (communicate in advance)

- [ ] Bring your own laptop (any OS — you only need SSH and a terminal).
- [ ] Clone the workshop repository.
- [ ] Familiarity with Python and basic Django concepts.
- [ ] Familiarity with JavaScript/React is helpful for the frontend section.

> **Note:** Pre-built cloud servers will be provided. Connection info (SSH credentials and URLs) will be distributed on paper at the start of the workshop — no local Tutor setup required.

---

## Open Questions & Facilitator Notes

- **Resolved — event design:** We settled on defining a *new* `REGISTRATION_DEMOGRAPHICS_CAPTURED` event rather than extending `STUDENT_REGISTRATION_COMPLETED`. Reasoning lives in the commit message of `upstream-patches/openedx-events.patch` and §5B above.
- **Resolved — entry-point scope:** Plugin registers under `lms.djangoapp` only (no `cms.djangoapp`). Reasoning lives in `backend/src/registration_demographics/apps.py` and §6 above.
- **frontend-base involvement:** Do we need any changes in `frontend-base` for the plugin slot, or is `@openedx/frontend-plugin-framework` sufficient? Clarify before the workshop.
- **Trivial backend example:** Decide whether to include the "server time" warm-up example or go straight into demographics to save time. Recommend: skip it if the audience is experienced; include it if the audience is mixed.
- **Scope of the event bus section:** Keep it to a brief mention. Participants interested in Kafka/Redis integration can follow up during the lab or after the workshop.
- **Aspects / xAPI:** Similarly, mention it as the "end of the pipeline" but don't live-code it. Point to Data Working Group resources.
- **Registration form specifically:** Since custom registration fields are not yet supported in the MFE port, this workshop could produce a real, mergeable contribution. Emphasize this to participants — their work today could ship.
