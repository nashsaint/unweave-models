#!/usr/bin/env bash
# Publish prepared, versioned model assets as a public GitHub Release.
set +x
set -euo pipefail
cd "$(dirname "$0")/.."
REPO=nashsaint/unweave-models
TAG="${1:-models-v1}"
[[ $TAG =~ ^models-v[0-9]+(\.[0-9]+)*$ ]] || { echo 'Use a versioned tag such as models-v1.' >&2; exit 1; }
OUT="dist/$TAG"
command -v gh >/dev/null || { echo 'Install GitHub CLI: brew install gh' >&2; exit 1; }
github() { python3 scripts/github_cli.py "$@"; }
github api user --jq .login >/dev/null
[[ $(github repo view "$REPO" --json isPrivate --jq .isPrivate) == false ]] \
  || { echo 'Model downloads need a public repository.' >&2; exit 1; }
python3 scripts/verify_models.py "$OUT" "$TAG"
# Never replace a published model: app versions pin the tag and checksums.
if state="$(github release view "$TAG" --repo "$REPO" --json isDraft --jq .isDraft 2>/dev/null)"; then
  [[ $state == true ]] || { echo 'This version is already published. Use a new model tag.' >&2; exit 1; }
else
  github release create "$TAG" --repo "$REPO" --draft --target "$(git rev-parse HEAD)" \
    --title "Unweave Core ML models $TAG" --notes-file RELEASE_NOTES.md
fi
github release upload "$TAG" --repo "$REPO" --clobber \
  "$OUT/htdemucs-fp32.zip" "$OUT/htdemucs_6s-fp32.zip" "$OUT/manifest.json" "$OUT/SHA256SUMS"
github release edit "$TAG" --repo "$REPO" --draft=false
printf 'Published: https://github.com/%s/releases/tag/%s\n' "$REPO" "$TAG"
