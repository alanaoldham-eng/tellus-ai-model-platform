#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UPSTREAM_DIR="${UPSTREAM_DIR:-"$ROOT_DIR/upstream"}"

mkdir -p "$UPSTREAM_DIR"
export GIT_LFS_SKIP_SMUDGE=1

MODELS=(
  "Qwen/Qwen3-Coder-Next"
  "Qwen/Qwen3-14B"
  "Qwen/Qwen3-32B"
)

for repo in "${MODELS[@]}"; do
  name="${repo##*/}"
  target="$UPSTREAM_DIR/$name"
  url="https://huggingface.co/$repo"

  if [ -d "$target/.git" ]; then
    echo "Updating $repo in $target"
    git -C "$target" fetch --tags --prune
  else
    echo "Cloning metadata for $repo into $target"
    git clone --filter=blob:none "$url" "$target"
  fi
done

echo "Upstream clones are in $UPSTREAM_DIR, which is ignored by Git."
echo "Preserve LICENSE, NOTICE, README, and attribution files for deployed revisions."

