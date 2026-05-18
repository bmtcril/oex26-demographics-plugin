#!/usr/bin/env bash

# Builds a clean, isolated Tutor dev environment for the OEX 2026 workshop.
# Covers E2E.md steps 3–5 (assumes step 1 "clone" and step 2 "branch checkout" are done).
#
# Usage (from repo root):
#   bash scripts/setup_dev.sh           # idempotent: skips destructive steps
#   bash scripts/setup_dev.sh --reset   # wipes .tutor_root and reinstalls packages
#
# All Tutor state is written to .tutor_root/ inside this repo — it won't
# interfere with any other Tutor installation on the machine.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export TUTOR_ROOT="$REPO_ROOT/.tutor_root"
VENV="$REPO_ROOT/.venv"

# Sibling repos expected one directory above this repo
PARENT="$(dirname "$REPO_ROOT")"
OPENEDX_PLATFORM="$PARENT/openedx-platform"
FRONTEND_AUTHN="$PARENT/frontend-app-authn"
OPENEDX_EVENTS="$PARENT/openedx-events"

WORKSHOP_BRANCH="bmtcril/oex26_conference_workshop"

RESET=false
if [[ "${1:-}" == "--reset" ]]; then
    RESET=true
fi

# ── Helpers ───────────────────────────────────────────────────────────────────

step() { echo; echo "══════════════════════════════════════════════"; echo "  $*"; echo "══════════════════════════════════════════════"; }
info() { echo "  → $*"; }
die()  { echo; echo "ERROR: $*" >&2; exit 1; }

# ── Pre-flight checks ─────────────────────────────────────────────────────────

step "Pre-flight checks"

for repo_path in "$OPENEDX_PLATFORM" "$FRONTEND_AUTHN" "$OPENEDX_EVENTS"; do
    repo_name="$(basename "$repo_path")"
    if [[ ! -d "$repo_path/.git" ]]; then
        die "Expected repo not found: $repo_path
  Clone it and check out the workshop branch before running this script."
    fi
    current_branch="$(git -C "$repo_path" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "(unknown)")"
    if [[ "$current_branch" != "$WORKSHOP_BRANCH" ]]; then
        die "$repo_name is on branch '$current_branch', expected '$WORKSHOP_BRANCH'.
  Run: git -C $repo_path checkout $WORKSHOP_BRANCH"
    fi
    info "Found $repo_name @ $WORKSHOP_BRANCH"
done

PYTHON_BIN="$VENV/bin/python"
if [[ ! -x "$PYTHON_BIN" ]]; then
    info "No virtual environment found at $VENV ... recreating."
    uv venv -p 3.12
fi
PYTHON_VERSION="$("$PYTHON_BIN" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
if [[ "$PYTHON_VERSION" != "3.12" ]]; then
    info "Virtual environment at $VENV is Python $PYTHON_VERSION, recreating at 3.12."
    rm -rf .venv
    uv venv -p 3.12
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"
info "Activated: $(python --version) at $(which python)"

info "TUTOR_ROOT=$TUTOR_ROOT"
info "RESET=$RESET"

# ── Stop any running Tutor dev instance ───────────────────────────────────────

step "Stopping any running Tutor dev instance"
if command -v tutor >/dev/null 2>&1; then
    tutor dev stop 2>/dev/null && info "Stopped." || info "Nothing was running — continuing."
else
    info "Tutor not yet installed — skipping stop."
fi

# ── Clean slate (--reset only) ────────────────────────────────────────────────

if [[ "$RESET" == true ]]; then
    step "Removing existing .tutor_root  [--reset]"
    rm -rf "$TUTOR_ROOT"
    info "Done."
else
    info "Skipping .tutor_root removal (pass --reset to wipe and start fresh)."
fi

# ── Install the Tutor plugin (--reset only) ─────────────────────────

if [[ "$RESET" == true ]]; then
    step "Installing Tutor, tutor-mfe, and the demographics plugin  [--reset]"
    # This pulls in the correct version of tutor and tutor-mfe, don't manage
    # them here.
    uv pip install -e "$REPO_ROOT/tutor_plugin"

    info "Enabling plugins..."
    tutor plugins enable mfe
    tutor plugins enable demographics_plugin
    echo
    tutor plugins list
else
    info "Skipping package installation (pass --reset to reinstall)."
fi

# ── Mount source directories ────────────────────────────────────────

step "Mounting source directories"
tutor mounts add "$REPO_ROOT/backend"         # our Django app (live-editable)
tutor mounts add "$OPENEDX_PLATFORM"          # patched openedx-platform
tutor mounts add "$FRONTEND_AUTHN"            # patched frontend-app-authn
tutor mounts add "$OPENEDX_EVENTS"            # patched openedx-events
echo
tutor mounts list

# ── Build images and launch ─────────────────────────────────────────


step "Launching tutor dev"
info "Running 'tutor dev launch' — migrations run automatically during init."
tutor dev launch

info "Creating admin use."
tutor dev do createuser --staff --superuser --password workshop oex_workshop workshop@oex.invalid
echo
echo "✔  Setup complete. See E2E.md for verification steps."
