#!/usr/bin/env bash

# Builds a clean, isolated Tutor dev environment for the OEX 2026 workshop.
# Covers E2E.md steps 3–5 (assumes step 1 "clone" and step 2 "patch" are done).
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

# Sibling repos expected one directory above this repo (as cloned in E2E §1)
PARENT="$(dirname "$REPO_ROOT")"
OPENEDX_PLATFORM="$PARENT/openedx-platform"
FRONTEND_AUTHN="$PARENT/frontend-app-authn"
OPENEDX_EVENTS="$PARENT/openedx-events"

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
    if [[ ! -d "$repo_path/.git" ]]; then
        die "Expected repo not found: $repo_path
  Clone it and apply the upstream patch before running this script.
  See E2E.md §1–2 for instructions."
    fi
    info "Found $(basename "$repo_path") at $repo_path"
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

# ── E2E §3 — Install the Tutor plugin (--reset only) ─────────────────────────

if [[ "$RESET" == true ]]; then
    step "E2E §3 — Installing Tutor, tutor-mfe, and the demographics plugin  [--reset]"
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

# ── E2E §4 — Mount source directories ────────────────────────────────────────

step "E2E §4 — Mounting source directories"
tutor mounts add "$REPO_ROOT/backend"         # our Django app (live-editable)
tutor mounts add "$OPENEDX_PLATFORM"          # patched openedx-platform
tutor mounts add "$FRONTEND_AUTHN"            # patched frontend-app-authn
tutor mounts add "$OPENEDX_EVENTS"            # patched openedx-events
echo
tutor mounts list

# ── E2E §5 — Build images and launch ─────────────────────────────────────────

#step "E2E §5 — Building images"
#info "Building openedx image (this takes a while)..."
#tutor images build openedx-dev

#info "Building mfe image (will retry up to 5 times on failure)..."
#for attempt in 1 2 3 4 5; do
#    tutor images build mfe-dev && break
#    if [[ $attempt -eq 5 ]]; then
#        die "mfe-dev image build failed after 5 attempts."
#    fi
#    info "Attempt $attempt failed — retrying in 10 seconds..."
#    sleep 10
#done

#info "Building openedx-authn-dev image..."
#tutor images build openedx-authn

# Only seems to be needed on verawood
#info "Building permissions image..."
#tutor images build permissions

step "E2E §5 — Launching tutor dev"
info "Running 'tutor dev launch' — migrations run automatically during init."
tutor dev launch

echo
echo "✔  Setup complete. See E2E.md §6–10 for verification steps."
