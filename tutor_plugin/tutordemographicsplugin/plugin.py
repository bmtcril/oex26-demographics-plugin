"""
Tutor plugin for the Open edX Registration Demographics Plugin.

Installs the backend Django app (openedx-registration-demographics-plugin from
PyPI) into the LMS image and configures the frontend plugin component
(DemographicsFields from openedx-demographics-plugin on npm) in the
frontend-app-authn registration form slot.

Requirements:
    tutor Verawood branch or release
    tutor-mfe (for frontend slot configuration — degrades gracefully if absent)
"""

from tutor import hooks

try:
    from tutormfe.hooks import PLUGIN_SLOTS

    _tutormfe_available = True
except ImportError:
    _tutormfe_available = False

# ---------------------------------------------------------------------------
# Backend: Install the Django app plugin into the LMS image
# ---------------------------------------------------------------------------

# If a directory named "backend" has been mounted with `tutor mounts add`,
# this maps it into the openedx[-dev] image and into the container's
# virtualenv. When no such directory is mounted this line has no effect,
# so it is safe in the production version of the plugin too.
hooks.Filters.MOUNTED_DIRECTORIES.add_item(("openedx", "backend"))

# The openedx-dockerfile-post-python-requirements patch runs after pip
# installs the base Open edX requirements. We install only into the LMS
# image here; CMS does not run registration code so we skip it.
#
# Workshop talking point: compare with sample-plugin which uses the same
# patch for both LMS and CMS. The right scope is a design decision.
hooks.Filters.ENV_PATCHES.add_item(
    (
        "openedx-lms-dockerfile-post-python-requirements",
        "RUN pip install openedx-registration-demographics-plugin",
    )
)

# ---------------------------------------------------------------------------
# Custom setup step, we don't need to do anything special on init but this is
# where it would happen
# ---------------------------------------------------------------------------

# hooks.Filters.CLI_DO_INIT_TASKS.add_item()

# ---------------------------------------------------------------------------
# Frontend: Install npm package and configure the authn registration slot
# ---------------------------------------------------------------------------
# Only runs when tutor-mfe is installed, so the plugin degrades gracefully
# if someone uses this plugin without the MFE plugin.
#
# Workshop talking point: this is the "graceful degradation" pattern —
# the backend filter/event still work without the MFE slot; operators
# who have a custom MFE can still collect demographics via the REST API.
# ---------------------------------------------------------------------------

if _tutormfe_available:
    # Step 1: Install the npm package into all MFE images.
    #
    # Ideally this would use mfe-dockerfile-post-npm-install-authn to scope
    # installation to frontend-app-authn only, but env.config.jsx is a single
    # shared file rendered for all MFEs. The buildtime import below must
    # resolve in every MFE's node_modules, so we install it globally.
    # hooks.Filters.ENV_PATCHES.add_item(
    #    (
    #        "mfe-dockerfile-post-npm-install",
    #        "RUN npm install 'openedx-demographics-plugin/@git+https://github.com/bmtcril/oex26-workshop.git/frontend'",
    #    )
    # )

    # Step 2: Import DemographicsFields in env.config.jsx so it is in scope
    # when the slot configuration is evaluated at runtime.
    hooks.Filters.ENV_PATCHES.add_item(
        (
            "mfe-env-config-buildtime-imports",
            "import { DemographicsFields } from 'openedx-demographics-plugin';",
        )
    )

    # Step 3: Register DemographicsFields against the registration slot.
    #
    # Slot ID: org.openedx.frontend.authn.register.additional_fields.v1
    # Props passed by the slot: formFields (current form values),
    #   setFormField (change handler)
    #
    # We use a plain Insert — no Hide — because the slot is empty by default;
    # there is no built-in widget to replace.
    PLUGIN_SLOTS.add_item(
        (
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
          },
        }""",
        )
    )
