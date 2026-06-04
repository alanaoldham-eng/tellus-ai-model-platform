#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODEL_STORAGE_DIR="${MODEL_STORAGE_DIR:-"$ROOT_DIR/models"}"
DOWNLOAD_MODE="${TELLUS_AI_DOWNLOAD_MODE:-metadata}"

mkdir -p "$MODEL_STORAGE_DIR"

if ! command -v huggingface-cli >/dev/null 2>&1; then
  echo "huggingface-cli is required. Install with: pip install huggingface_hub"
  exit 1
fi

download_model() {
  local repo="$1"
  local name="${repo##*/}"
  local target="$MODEL_STORAGE_DIR/$name"

  echo "Downloading $repo into $target with mode=$DOWNLOAD_MODE"
  if [ "$DOWNLOAD_MODE" = "full" ]; then
    huggingface-cli download "$repo" --local-dir "$target"
  else
    huggingface-cli download "$repo" \
      --local-dir "$target" \
      --include "README.md" "LICENSE*" "NOTICE*" "config.json" "tokenizer*" "*.json"
  fi
}

download_model "Qwen/Qwen3-Coder-Next"
download_model "Qwen/Qwen3-14B"
download_model "Qwen/Qwen3-32B"

echo "Downloads are in $MODEL_STORAGE_DIR, which is ignored by Git."
echo "Set TELLUS_AI_DOWNLOAD_MODE=full only when you intentionally want model weights locally."

