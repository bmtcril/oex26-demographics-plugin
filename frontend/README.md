# Frontend — `openedx-demographics-plugin`

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
├── package.json               ← package metadata + peer deps
├── babel.config.js            ← Babel config (React, current Node)
├── jest.config.js             ← Jest config (jsdom, Paragon mock)
├── src/
│   ├── index.js               ← re-exports DemographicsFields as default
│   └── DemographicsFields.jsx ← the plugin component
└── __mocks__/
    └── @openedx/paragon.js    ← minimal Paragon mock for Jest
```

## Installing for development

The package uses a local install — it is never published to the npm registry.
Inside the `authn` MFE container (or locally with `tutor mounts`):

```bash
npm install /path/to/frontend
```

Or, with the Tutor plugin in this repo enabled, the install runs automatically
during `tutor dev launch` via the `mfe-dockerfile-post-npm-install` patch.

## Running tests

```bash
cd frontend
npm test              # run once
npm run test:coverage # with coverage report
```

Tests do not require a running MFE or Tutor environment — Paragon is mocked
via `__mocks__/@openedx/paragon.js`.

## How the component loads

1. The Tutor plugin patches `mfe-dockerfile-post-npm-install` to `npm install`
   this package into the `authn` MFE image at build time.
2. The `mfe-env-config-buildtime-imports` patch adds
   `import DemographicsFields from 'openedx-demographics-plugin'` to
   `env.config.jsx`, making the component available by name in the slot config.
3. The `PLUGIN_SLOTS.add_item(...)` patch registers `DemographicsFields`
   against slot ID `org.openedx.frontend.authn.register.additional_fields.v1`
   at runtime, passing `formFields` and `setFormField` as `pluginProps`.

## Props

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `formFields` | `Record<string, string>` | yes | Current registration form values, keyed by field name. |
| `setFormField` | `Function` | yes | Change handler; called with a synthetic event whose `target` has `name` and `value`. Matches the handler signature already used by the authn MFE form. |
| `departments` | `Array<{value, label}>` | no | Overrides the default department list. Pass via `pluginProps` in `env.config.jsx` to customise options without forking the component. |
