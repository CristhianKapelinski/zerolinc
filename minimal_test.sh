#!/usr/bin/env bash
# Minimal test: the offline unit suite, then one real zero-shot classification of the
# bundled sample tickets. Exercises the whole path a user takes, not --help.
#
# The first run downloads the default zero-shot checkpoint (~0.8 GB) from the HuggingFace
# Hub; later runs are offline. Nothing is written outside this directory.
set -euo pipefail
cd "$(dirname "$0")"

for t in git uv; do
  command -v "$t" >/dev/null 2>&1 || {
    echo "missing required tool: $t" >&2
    [ "$t" = uv ] && echo "  install it: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
    exit 1; }
done

echo "== [1/2] unit suite (offline, no model) =="
uv run --extra dev pytest -q

echo
echo "== [2/2] classifying the bundled sample with the zero-shot engine =="
uv run zerolinc classify --input examples/tickets_sample.csv --engine zeroshot

echo
echo "MINIMAL TEST: PASSED"
