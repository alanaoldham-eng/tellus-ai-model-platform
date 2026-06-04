#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODEL_STORAGE_DIR="${MODEL_STORAGE_DIR:-"$ROOT_DIR/models"}"
STATUS=0

required_repo_files=(
  "$ROOT_DIR/LICENSE"
  "$ROOT_DIR/LICENSES/README.md"
  "$ROOT_DIR/LICENSES/upstream-models.md"
  "$ROOT_DIR/docs/licensing.md"
)

for file in "${required_repo_files[@]}"; do
  if [ ! -f "$file" ]; then
    echo "Missing required license documentation: $file"
    STATUS=1
  fi
done

if [ -d "$MODEL_STORAGE_DIR" ]; then
  for dir in "$MODEL_STORAGE_DIR"/*; do
    [ -d "$dir" ] || continue
    if [ ! -f "$dir/README.md" ]; then
      echo "Missing README.md for downloaded model directory: $dir"
      STATUS=1
    fi
    if ! compgen -G "$dir/LICENSE*" >/dev/null; then
      echo "Missing LICENSE file for downloaded model directory: $dir"
      STATUS=1
    fi
  done
else
  echo "No local model storage found at $MODEL_STORAGE_DIR. This is OK for mock/local API tests."
fi

if [ "$STATUS" -eq 0 ]; then
  echo "License documentation checks passed."
fi

exit "$STATUS"

