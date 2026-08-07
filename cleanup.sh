#!/usr/bin/env bash
# Removes everything a run of this artifact created, inside the clone and outside it.
# It never touches anything tracked by git, and never removes the clone itself.
#
#   ./cleanup.sh --dry-run   list what would be removed, delete nothing
#   ./cleanup.sh             remove it
set -euo pipefail
cd "$(dirname "$0")"

DRY=0
[ "${1:-}" = "--dry-run" ] && DRY=1

total=0
gone() {   # gone <path> <what it is>
  local p="$1" what="$2" sz
  [ -e "$p" ] || return 0
  sz=$(du -sm "$p" 2>/dev/null | cut -f1); sz=${sz:-0}
  total=$((total + sz))
  printf '  %-40s %6s MB  %s\n' "$p" "$sz" "$what"
  [ "$DRY" = "1" ] || rm -rf "$p"
}

echo "Removing what a run of this artifact leaves behind:"
gone .venv            "the Python environment"
gone .pytest_cache    "test cache"
gone .ruff_cache      "lint cache"
gone predictions.csv  "output of the minimal test"
gone benchmark        "the companion evaluation repository the claims clone, and its environment"

# The model checkpoints are the largest thing a run downloads. They land in the shared
# HuggingFace cache, which usually holds models this artifact never asked for, so they go
# only when that cache is inside the clone: deleting a cache the rest of the machine uses
# is not this script's business.
CACHE="${HF_HUB_CACHE:-${HF_HOME:-$HOME/.cache/huggingface}}"
case "$(readlink -f "$CACHE" 2>/dev/null)/" in
  "$PWD"/*) gone "$CACHE" "the model cache (inside the clone)" ;;
  *) if [ -e "$CACHE" ]; then
       sz=$(du -sm "$CACHE" 2>/dev/null | cut -f1)
       echo "  (kept: $CACHE, ${sz:-?} MB of models, shared with the rest of this machine;"
       echo "   remove it yourself, or point HF_HUB_CACHE inside the clone before running)"
     fi ;;
esac

echo
if [ "$DRY" = "1" ]; then
  echo "Dry run: nothing was removed. ${total} MB would be freed."
else
  echo "Done. ${total} MB freed. Nothing tracked by git was touched."
fi
