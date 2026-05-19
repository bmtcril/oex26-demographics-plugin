# End-to-End Smoke Test

This guide gets you from a fresh clone to a working demographics feature in a Tutor dev environment. Budget ~20 minutes — most of that is image builds.

---

## Prerequisites

- A Python 3.12 virtual environment activated

---

## 1. Clone and position

Clone all four repos as siblings, using the workshop branch for the three upstream repos:

```bash
git clone --branch bmtcril/oex26_conference_workshop https://github.com/openedx/openedx-platform.git
git clone --branch bmtcril/oex26_conference_workshop https://github.com/openedx/frontend-app-authn.git
git clone --branch bmtcril/oex26_conference_workshop https://github.com/openedx/openedx-events.git
git clone https://github.com/bmtcril/oex26-demographics-plugin.git
cd oex26-demographics-plugin
```

---

## 2. Workshop branches — what each one adds

The plugin's filter step, event receiver, and REST API all work without the upstream changes. The workshop branches add things that aren't in mainline yet:

| Branch | What it adds | Without it |
|--------|--------------|------------|
| `openedx-events` @ `bmtcril/oex26_conference_workshop` | `REGISTRATION_DEMOGRAPHICS_CAPTURED` signal definition | Receiver logs a warning and is a no-op |
| `openedx-platform` @ `bmtcril/oex26_conference_workshop` | Fires that event after successful registration | Event never fires |
| `frontend-app-authn` @ `bmtcril/oex26_conference_workshop` | Plugin slot in the registration form using the code from "frontend" | Demographics fields don't appear in the MFE |

Verify the correct branches are checked out before continuing:

```bash
for repo in ../openedx-platform ../frontend-app-authn ../openedx-events; do
    echo "$(basename $repo): $(git -C $repo rev-parse --abbrev-ref HEAD)"
done
# Each should print: bmtcril/oex26_conference_workshop
```

---

## 3. Install the Tutor plugin

If not already enabled, the `mfe` plugin must be enabled as well.

```bash
# From the repo root — install the tutor plugin package into tutor's Python env
# this will also install tutor and tutor-mfe @ main
pip install -e ./tutor_plugin

tutor plugins enable demographics_plugin
tutor plugins enable mfe
tutor plugins list   # demographics_plugin and mfe should appear as enabled
```

---

## 4. Mount the backend and the workshop-branch upstream repos

This adds the local source directories to Tutor so they are mapped into the
images below. The mounted `frontend-app-authn` workshop branch is what
provides the `module.config.js` `localModules` alias and the `env.config.jsx`
slot registration that pull in `DemographicsFields` from this repo's
`frontend/` directory - see [`frontend/README.md`](./frontend/README.md) and
[`tutor_plugin/README.md`](./tutor_plugin/README.md) for the full mechanism.

```bash
tutor mounts add ./backend            # this repo's Django plugin (editable install)
tutor mounts add ../openedx-platform  # workshop branch - fires the new filter/event
tutor mounts add ../frontend-app-authn # workshop branch - imports + registers DemographicsFields
tutor mounts add ../openedx-events    # workshop branch - defines REGISTRATION_DEMOGRAPHICS_CAPTURED
tutor mounts list
```

---

## 5. Build images and launch

```bash
tutor dev launch
```

`tutor dev launch` runs `init` internally, which applies all pending Django
migrations including `registration_demographics` - the plugin is in
`INSTALLED_APPS` via its `lms.djangoapp` entry point, so no manual `migrate`
step is needed.

---

## 6. Verify the frontend fields

1. Open `http://local.openedx.io/register` in a browser.
2. Scroll down - a **Pronouns** text field and a **Department** dropdown should appear just above the Create Account button.
3. If the fields are missing, the mounted `frontend-app-authn` is probably not on the workshop branch (its `env.config.jsx` is what imports `DemographicsFields`). Verify with:

   ```bash
   git -C ../frontend-app-authn rev-parse --abbrev-ref HEAD   # expect: bmtcril/oex26_conference_workshop
   tutor dev exec authn cat /openedx/app/env.config.jsx | grep DemographicsFields
   ```

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
