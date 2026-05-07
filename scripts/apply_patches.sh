#!/usr/bin/env bash
# scripts/apply_patches.sh
#
# Applies the upstream patches from upstream-patches/ to the sibling
# repository checkouts expected one directory above this repo (as cloned
# in E2E.md §1).
#
# Usage (from repo root):
#   bash scripts/apply_patches.sh
#
# Safe to re-run: each patch is checked before applying and skipped if
# the target commit is already present in the repo's history.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PATCHES_DIR="$REPO_ROOT/upstream-patches"
PARENT="$(dirname "$REPO_ROOT")"

OPENEDX_PLATFORM="$PARENT/openedx-platform"
FRONTEND_AUTHN="$PARENT/frontend-app-authn"
OPENEDX_EVENTS="$PARENT/openedx-events"

# ── Helpers ───────────────────────────────────────────────────────────────────

step() { echo; echo "══════════════════════════════════════════════"; echo "  $*"; echo "══════════════════════════════════════════════"; }
info() { echo "  → $*"; }
skip() { echo "  ✔ $* (already applied — skipping)"; }
die()  { echo; echo "ERROR: $*" >&2; exit 1; }

# apply_patch <repo_dir> <patch_file>
#
# Uses `git apply --check` to test whether the patch can be applied cleanly.
# If the check fails it means either the patch is already applied or the
# target has diverged; we distinguish the two cases by trying `--reverse`.
apply_patch() {
    local repo="$1"
    local patch="$2"
    local name
    name="$(basename "$patch")"

    info "Checking $name against $(basename "$repo")..."

    # Already applied? (reverse-apply succeeds)
    if git -C "$repo" apply --check --reverse "$patch" 2>/dev/null; then
        skip "$name"
        return
    fi

    # Can it be applied cleanly?
    if ! git -C "$repo" apply --check "$patch" 2>/dev/null; then
        die "$name does not apply cleanly to $(basename "$repo").
  The upstream repo may have diverged from what the patch expects.
  Review the diff manually — each patch's commit message explains what to add and where:
    less $patch
  To abort a failed git am mid-flight:
    git -C $repo am --abort"
    fi

    git -C "$repo" am "$patch"
    info "Applied $name."
}

# ── Pre-flight ────────────────────────────────────────────────────────────────

step "Pre-flight checks"

for repo_path in "$OPENEDX_PLATFORM" "$FRONTEND_AUTHN" "$OPENEDX_EVENTS"; do
    if [[ ! -d "$repo_path/.git" ]]; then
        die "Expected repo not found: $repo_path
  Clone it before running this script. See E2E.md §1 for instructions."
    fi
    info "Found $(basename "$repo_path") at $repo_path"
done

# ── Apply patches ─────────────────────────────────────────────────────────────

step "Applying patches"

apply_patch "$OPENEDX_EVENTS"    "$PATCHES_DIR/openedx-events.patch"
apply_patch "$OPENEDX_PLATFORM"  "$PATCHES_DIR/edx-platform.patch"
apply_patch "$FRONTEND_AUTHN"    "$PATCHES_DIR/frontend-app-authn.patch"

echo
echo "✔  All patches applied. You can now run scripts/setup_dev.sh."
