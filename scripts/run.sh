#!/usr/bin/env bash

# Just runs checks and launches the Tutor dev environment.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export TUTOR_ROOT="$REPO_ROOT/.tutor_root"
VENV="$REPO_ROOT/.venv"

# Sibling repos expected one directory above this repo
PARENT="$(dirname "$REPO_ROOT")"
OPENEDX_PLATFORM="$PARENT/openedx-platform"
FRONTEND_AUTHN="$PARENT/frontend-app-authn"
OPENEDX_EVENTS="$PARENT/openedx-events"

# ── Helpers ───────────────────────────────────────────────────────────────────

step() { echo; echo "══════════════════════════════════════════════"; echo "  $*"; echo "══════════════════════════════════════════════"; }
info() { echo "  → $*"; }
die()  { echo; echo "ERROR: $*" >&2; exit 1; }

# ── Pre-flight checks ─────────────────────────────────────────────────────────

step "Pre-flight checks"

for repo_path in "$OPENEDX_PLATFORM" "$FRONTEND_AUTHN" "$OPENEDX_EVENTS"; do
    if [[ ! -d "$repo_path/.git" ]]; then
        die "Expected repo not found: $repo_path
  Clone it and check out the workshop branch before continuing."
    fi
    info "Found $(basename "$repo_path") at $repo_path"
done

# shellcheck disable=SC1091
source "$VENV/bin/activate"
info "Activated: $(python --version) at $(which python)"

info "TUTOR_ROOT=$TUTOR_ROOT"

# ── Stop any running Tutor dev instance ───────────────────────────────────────

step "Stopping any running Tutor dev instance"
if command -v tutor >/dev/null 2>&1; then
    tutor dev stop 2>/dev/null && info "Stopped." || info "Nothing was running — continuing."
else
    info "Tutor not yet installed — skipping stop."
fi

step "Launching tutor dev"
info "Running 'tutor dev launch'"
tutor dev launch
