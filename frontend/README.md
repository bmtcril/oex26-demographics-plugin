# Frontend - `@openedx/openedx-demographics-plugin`

This directory is a small React package that provides the plugin component for
the workshop's registration demographics example.

It implements the frontend half of the demographics feature:

- a `DemographicsFields` component that renders **Pronouns** and **Department**
  fields into the `org.openedx.frontend.authn.register.additional_fields.v1`
  plugin slot
- an optional `departments` prop so operators can supply their own list without
  forking the component.

## Layout

```text
frontend/
├── package.json                    ← package metadata + peer deps
├── babel.config.js                 ← Babel config (React, current Node)
├── jest.config.js                  ← Jest config (jsdom, Paragon mock)
├── src/
│   ├── index.js                    ← re-exports DemographicsFields as default
│   ├── DemographicsFields.jsx      ← the plugin component
│   └── DemographicsFields.test.jsx ← Jest + Testing Library coverage
└── __mocks__/
    └── @openedx/paragon.js         ← minimal Paragon mock for Jest
```

## Installing

This package has two install paths, one for workshop / development and one
for production. The Tutor plugin in this repo ships configured for the
development path; the production patches are present but commented out in
[`tutor_plugin/tutordemographicsplugin/plugin.py`](../tutor_plugin/tutordemographicsplugin/plugin.py).

### Development (current default)

The `authn` MFE on the `bmtcril/oex26_conference_workshop` branch of
`frontend-app-authn` resolves this package via its `module.config.js`:

```js
// frontend-app-authn/module.config.js (workshop branch)
module.exports = {
  localModules: [
    {
      moduleName: "@openedx/openedx-demographics-plugin",
      dir: "/path/to/oex26-demographics-plugin/frontend",
      dist: "src",
    },
  ],
};
```

Frontend Plugin Framework's webpack config reads `localModules` and aliases
the bare import `@openedx/openedx-demographics-plugin` to this directory's
`src/`, so the `authn` dev server picks up source edits with hot module
reload. No `npm install` of this package into the MFE is required -
`package.json` here is only used for its peer deps and the Jest test setup;
the `localModules` alias overrides anything that would normally resolve
through `node_modules`.

The slot is then wired up in `env.config.jsx` on the same workshop branch,
which imports `DemographicsFields` by that module name and registers it
against `org.openedx.frontend.authn.register.additional_fields.v1`.

### Production

For a non-mounted deployment, publish this package to npm (as
`@openedx/openedx-demographics-plugin`) and uncomment the two patches in
`tutor_plugin/tutordemographicsplugin/plugin.py`:

- `mfe-dockerfile-post-npm-install` - `RUN npm install @openedx/openedx-demographics-plugin` into every MFE image at build time.
- `mfe-env-config-buildtime-imports` - inject `import { DemographicsFields } from '@openedx/openedx-demographics-plugin';` into the generated `env.config.jsx`.

The `PLUGIN_SLOTS.add_item(...)` call in the same plugin file is already
active and registers the widget against the slot at runtime, so once those
two build-time patches are enabled the MFE image is self-contained - no
source mount, no workshop branch of `frontend-app-authn` required.

## Running tests

```bash
cd frontend
npm test              # run once
npm run test:coverage # with coverage report
```

Tests do not require a running MFE or Tutor environment — Paragon is mocked
via `__mocks__/@openedx/paragon.js`.

## How the component loads

### In development (mounted `frontend-app-authn`)

1. `tutor mounts add` for `frontend-app-authn` makes the workshop branch
   the source tree the `authn` dev server runs against.
2. That branch's `module.config.js` aliases `@openedx/openedx-demographics-plugin`
   to this directory; the webpack dev server rebuilds and hot-reloads on
   any change under `frontend/src/`.
3. That branch's `env.config.jsx` imports `DemographicsFields` from the
   aliased module name and registers it against
   `org.openedx.frontend.authn.register.additional_fields.v1`.

In this mode the Tutor plugin's `PLUGIN_SLOTS.add_item(...)` call still
fires, but the meaningful slot registration is the one in the mounted
`env.config.jsx`.

### In production (npm-published)

1. The Tutor plugin's `mfe-dockerfile-post-npm-install` patch runs
   `npm install @openedx/openedx-demographics-plugin` into every MFE image
   at build time.
2. The `mfe-env-config-buildtime-imports` patch injects
   `import { DemographicsFields } from '@openedx/openedx-demographics-plugin';`
   into the generated `env.config.jsx`, making the component available by
   name in the slot config.
3. The `PLUGIN_SLOTS.add_item(...)` patch registers `DemographicsFields`
   against slot ID `org.openedx.frontend.authn.register.additional_fields.v1`
   at runtime, passing `formFields` and `setFormField` as `pluginProps`.

## Props

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `formFields` | `Record<string, string>` | yes | Current registration form values, keyed by field name. |
| `setFormField` | `Function` | yes | Change handler; called with a synthetic event whose `target` has `name` and `value`. Matches the handler signature already used by the authn MFE form. |
| `departments` | `Array<{value, label}>` | no | Overrides the default department list. Pass via `pluginProps` in `env.config.jsx` to customise options without forking the component. |
