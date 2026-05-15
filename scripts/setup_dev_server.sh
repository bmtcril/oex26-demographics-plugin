#!/usr/bin/env bash

# Builds a clean, isolated Tutor environment on a fresh Ubuntu server.
#
# Prerequisites from a brand new Ubuntu server:
#   - mkdir dev
#   - cd dev
#   - git clone https://github.com/bmtcril/oex26-demographics-plugin

# Then run:
#   ./oex26-demographics-plugin/scripts/setup_dev_server.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export TUTOR_ROOT="$REPO_ROOT/.tutor_root"
VENV="$REPO_ROOT/.venv"

# Sibling repos expected one directory above this repo (as cloned in E2E §1)
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

# ── Ensure uv is available ───────────────────────────────────────────────────

if ! command -v uv >/dev/null 2>&1; then
    echo "  → uv not found — installing via astral.sh ..."
    curl -LsSf https://astral.sh/uv/install.sh | sh > /dev/null
    # The installer adds ~/.local/bin to PATH in shell rc files but not the
    # current session, so source the env script it drops if present.
    # shellcheck disable=SC1091
    [[ -f "$HOME/.local/bin/env" ]] && source "$HOME/.local/bin/env"
    command -v uv >/dev/null 2>&1 || export PATH="$HOME/.local/bin:$PATH"
fi

# ── Ensure npm is available ──────────────────────────────────────────────────

if ! command -v npm >/dev/null 2>&1; then
    echo "  → npm not found — installing via apt ..."
    sudo apt-get install -y npm
fi

# ── Ensure Docker is available ───────────────────────────────────────────────

if ! command -v docker >/dev/null 2>&1; then
    echo "  → Docker not found — installing via get.docker.com ..."
    curl -fsSL https://get.docker.com | sh
fi

# Ensure the current user is in the docker group so Tutor can run without sudo.
# If not, add them and re-exec under the new group — avoids needing to log out.
# The re-execed process will already have docker in its groups, so this runs
# at most once.
if ! groups | grep -qw docker; then
    echo "  → Adding $USER to docker group and re-launching under new group ..."
    sudo usermod -aG docker "$USER"
    exec sg docker "$0 $*"
fi

info "REPO_ROOT: $REPO_ROOT"
info "TUTOR_ROOT: $TUTOR_ROOT"
info "VENV: $VENV"
info "uv $(uv --version)"
info "docker $(docker --version)"

# ── Pre-flight checks ─────────────────────────────────────────────────────────

step "Pre-flight checks"

if [[ "$RESET" == true ]]; then
    echo
    echo "  WARNING: --reset will hard-reset all three workshop repos to origin."
    echo "  Any local changes in the following directories will be permanently lost:"
    for repo_path in "$OPENEDX_PLATFORM" "$FRONTEND_AUTHN" "$OPENEDX_EVENTS"; do
        echo "    $repo_path"
    done
    echo
    read -r -p "  Continue? [y/N] " _confirm
    if [[ "$_confirm" != "y" && "$_confirm" != "Y" ]]; then
        echo "Aborted."
        exit 0
    fi
fi

# ── Clone or verify workshop repos ───────────────────────────────────────────

step "Workshop repository setup"

for repo_path in "$OPENEDX_PLATFORM" "$FRONTEND_AUTHN" "$OPENEDX_EVENTS"; do
    repo_name="$(basename "$repo_path")"
    remote_url="https://github.com/openedx/${repo_name}.git"

    if [[ ! -d "$repo_path/.git" ]]; then
        info "Cloning $repo_name @ $WORKSHOP_BRANCH ..."
        git clone --depth 1 --branch "$WORKSHOP_BRANCH" "$remote_url" "$repo_path"
    elif [[ "$RESET" == true ]]; then
        info "Hard-resetting $repo_name to origin/$WORKSHOP_BRANCH ..."
        git -C "$repo_path" fetch origin
        git -C "$repo_path" checkout "$WORKSHOP_BRANCH"
        git -C "$repo_path" reset --hard "origin/$WORKSHOP_BRANCH"
    else
        current_branch="$(git -C "$repo_path" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "(unknown)")"
        if [[ "$current_branch" != "$WORKSHOP_BRANCH" ]]; then
            die "$repo_name is on branch '$current_branch', expected '$WORKSHOP_BRANCH'.
  Run: git -C $repo_path checkout $WORKSHOP_BRANCH
  Or re-run with --reset to hard-reset all repos to origin."
        fi
        info "Found $repo_name @ $WORKSHOP_BRANCH"
    fi
done

PYTHON_BIN="$VENV/bin/python"
if [[ ! -x "$PYTHON_BIN" ]]; then
    info "No virtual environment found at $VENV ... recreating."
    uv venv -p 3.12 $VENV
fi
PYTHON_VERSION="$("$PYTHON_BIN" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
if [[ "$PYTHON_VERSION" != "3.12" ]]; then
    info "Virtual environment at $VENV is Python $PYTHON_VERSION, recreating at 3.12."
    rm -rf .venv
    uv venv -p 3.12 $VENV
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

if [[ "$RESET" == true ]] || ! command -v tutor >/dev/null 2>&1; then
    step "E2E §3 — Installing Tutor, tutor-mfe, and the demographics plugin"
    # This pulls in the correct version of tutor and tutor-mfe, don't manage
    # them here.
    uv pip install -e "$REPO_ROOT/tutor_plugin"

    info "Enabling plugins..."
    tutor plugins enable mfe
    tutor plugins enable demographics_plugin
    echo
    tutor plugins list
else
    info "Tutor already installed — skipping package installation (pass --reset to reinstall)."
fi

# ── E2E §4 — Mount backend source directories ────────────────────────────────────────
# Note: Frontend mount has to happen AFTER the first build of mfe
step "E2E §4 — Mounting source directories"
tutor mounts add "$REPO_ROOT/backend"         # our Django app (live-editable)
tutor mounts add "$OPENEDX_PLATFORM"          # workshop branch of openedx-platform
tutor mounts add "$OPENEDX_EVENTS"            # workshop branch of openedx-events
echo
tutor mounts list

# ── E2E §5 — Build images and launch ─────────────────────────────────────────


step "E2E §5 — tutor dev"
info "Running build images."
tutor images build openedx mfe-dev authn-dev

# ── E2E §4 — Build and mount frontend source directory───────────────────────
npm --prefix "$FRONTEND_AUTHN" ci "$FRONTEND_AUTHN"
tutor mounts add "$FRONTEND_AUTHN"            # workshop branch of frontend-app-authn

info "Running dev init."
tutor dev do init

ifno "Stopping tutor services."
tutor dev stop

info "Creating admin user."
tutor dev do createuser --staff --superuser --password workshop oex_workshop workshop@oex.invalid
echo
echo "✔  Setup complete. Run 'tutor dev start -d' to run everything in the background."
