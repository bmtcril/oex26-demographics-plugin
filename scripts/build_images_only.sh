#!/usr/bin/env bash

# Just does the image building steps of setup_dev due to the usual
# issues building tutor-mfe

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export TUTOR_ROOT="$REPO_ROOT/.tutor_root"
VENV="$REPO_ROOT/.venv"

# ── Helpers ───────────────────────────────────────────────────────────────────

step() { echo; echo "══════════════════════════════════════════════"; echo "  $*"; echo "══════════════════════════════════════════════"; }
info() { echo "  → $*"; }
die()  { echo; echo "ERROR: $*" >&2; exit 1; }

tutor config save

step "Building images"
info "Building openedx image (this takes a while)..."
tutor images build openedx-dev

info "Building mfe images (will retry up to 5 times on failure)..."
for attempt in 1 2 3 4 5; do
    tutor images build mfe-dev && break
    if [[ $attempt -eq 5 ]]; then
        die "mfe-dev image build failed after 5 attempts."
    fi
    info "Attempt $attempt failed — retrying in 10 seconds..."
    sleep 10
done

info "Building authn dev image (core MFEs are not auto-built by tutor dev launch)..."
tutor images build authn-dev




echo
echo "✔  Build complete. The rest of setup should work now."
