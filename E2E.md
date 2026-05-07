# End-to-End Smoke Test

This guide gets you from a fresh clone to a working demographics feature in a Tutor dev environment. Budget ~20 minutes — most of that is image builds.

---

## Prerequisites

- Tutor ≥ 20 with a working `tutor dev` environment
- [`tutor-mfe`](https://github.com/overhangio/tutor-mfe) installed and enabled

---

## 1. Clone and position

```bash
git clone https://github.com/openedx/openedx-platform.git
git clone https://github.com/openedx/frontend-app-authn.git
git clone https://github.com/openedx/openedx-events.git
git clone https://github.com/bmtcril/oex26-demographics-plugin.git
cd oex26-demographics-plugin
```

---

## 2. Apply the upstream patches

The plugin's filter step, event receiver, and REST API all work without the patches. The patches add two things that aren't in mainline yet:

| Patch | What it adds | Without it |
|-------|--------------|------------|
| `openedx-events.patch` | `REGISTRATION_DEMOGRAPHICS_CAPTURED` signal definition | Receiver logs a warning and is a no-op |
| `edx-platform.patch` | Fires that event after successful registration | Event never fires |
| `frontend-app-authn.patch` | Plugin slot in the registration form | Demographics fields don't appear in the MFE |

We assume you have the `frontend-app-authn`, `openedx-events`, and `edx-platform` repositories checked out one directory above this one, but the paths below can be adjusted as needed.

```bash
# In your frontend-app-authn checkout:
git am /path/to/oex26-demographics-plugin/upstream-patches/frontend-app-authn.patch

# In your openedx-events checkout:
git am /path/to/oex26-demographics-plugin/upstream-patches/openedx-events.patch

# In your edx-platform checkout:
git am /path/to/oex26-demographics-plugin/upstream-patches/edx-platform.patch
```

If the patches don't apply cleanly (upstream has moved), review the diffs manually — each commit message explains exactly what to add and where.

---

## 3. Install the Tutor plugin

If not already enabled, the `mfe` plugin must be enabled as well.

```bash
# From the repo root — install the tutor plugin package into tutor's Python env
pip install -e ./tutor_plugin

tutor plugins enable demographics_plugin
tutor plugins list   # demographics_plugin and mfe should appear as enabled
```

---

## 4. Mount the backend and authn MFE for live edits

This adds our local patched source directories to the Tutor so they will be 
built into the images below.

```bash
tutor mounts add ./backend  # the backend Django plugin from this repo
tutor mounts add ../openedx-platform
tutor mounts add ../frontend-app-authn
tutor mounts add ../openedx-events
tutor mounts list   
```

---

## 5. Build images and launch

```bash
tutor images build openedx   # installs the backend Django app into the LMS image
tutor images build mfe       # installs the npm package into the authn MFE
tutor dev launch
```

`tutor dev launch` runs `init` internally, which applies all pending Django migrations including `registration_demographics`. No manual migration step is needed.

---

## 6. Verify the frontend fields

1. Open `http://local.openedx.io/register` in a browser.
2. Scroll down — a **Pronouns** text field and a **Department** dropdown should appear just above the Create Account button.
3. If the fields are missing: `tutor dev exec authn cat /openedx/app/env.config.jsx | grep DemographicsFields` — if it's absent, rebuild the MFE image (`tutor images build mfe && tutor dev restart mfe`).

---

## 7. Verify the filter rejects bad input

Submit the registration form with **Department** set to anything not in `["eng", "ops", "edu"]` (or type it directly via curl):

```bash
curl -s -X POST http://local.openedx.io/api/user/v1/account/registration/ \
  -d "username=testfilter&email=tf@example.com&password=Test1234!&name=Test&department=badvalue" \
  | python3 -m json.tool
```

Expected: HTTP 400 with `"error_code": "invalid_department"`.

---

## 8. Verify the event fires

In a second terminal, tail LMS logs before registering:

```bash
tutor dev logs -f lms
```

Register a new user (via the form or curl) with a valid department. Look for a log line containing `RegistrationDemographicsCaptured` or the signal name `org.openedx.learning.registration.demographics.captured.v1`.

---

## 9. Verify the REST API

```bash
# Get a JWT for the user you just registered (replace credentials)
TOKEN=$(curl -s -X POST http://local.openedx.io/api/user/v1/account/login_session/ \
  -d "email=<email>&password=<password>" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -s -H "Authorization: Bearer $TOKEN" \
  http://local.openedx.io/api/registration-demographics/v1/me/ | python3 -m json.tool
```

Expected response:

```json
{
  "user": <user_id>,
  "pronouns": "<whatever was entered>",
  "department": "eng",
  "created": "...",
  "modified": "..."
}
```

---

## 10. Verify the admin UI

Log in as a superuser and open:

```
http://local.openedx.io/admin/registration_demographics/learnerdemographics/
```

The record created during registration should appear there with the correct pronouns and department.

---

## Quick check table

| What | Where | Pass condition |
|------|-------|----------------|
| Form fields visible | `/register` in browser | Pronouns + Department shown above submit button |
| Filter rejects bad dept | `curl` POST with `department=bogus` | HTTP 400, `error_code: invalid_department` |
| Filter passes good dept | `curl` POST with `department=eng` | Registration succeeds |
| Event fires | LMS log tail | Signal name in logs after registration |
| DB record created | Django admin | Row in `LearnerDemographics` with correct values |
| REST API returns data | `GET /api/registration-demographics/v1/me/` | 200 with pronouns + department |
