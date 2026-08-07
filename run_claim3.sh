#!/usr/bin/env bash
# Claim #3: the default zero-shot engine costs seconds and under 3 Wh.
# Fetches the evaluation artifact (companion repo) automatically and runs the
# cost check (live if a GPU is present). One command, no manual steps.
set -euo pipefail
cd "$(dirname "$0")"
# The evaluation run of record lives in the companion repository, pinned to the exact
# commit this artifact was evaluated at: a later change there cannot alter what you
# reproduce here.
BENCH_REPO="${ZEROLINC_BENCHMARK_REPO:-https://github.com/CristhianKapelinski/zerolinc-benchmark}"
BENCH_COMMIT="${ZEROLINC_BENCHMARK_COMMIT:-37ef42fd73a3685482e40d63e647abf44769dd6d}"

for t in git uv; do
  command -v "$t" >/dev/null 2>&1 || {
    echo "missing required tool: $t" >&2
    [ "$t" = uv ] && echo "  install it: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
    exit 1; }
done

if [ ! -d benchmark ]; then
  git clone -q "$BENCH_REPO" benchmark
  git -C benchmark checkout -q "$BENCH_COMMIT"
fi
cd benchmark && uv sync -q --extra dev && ./run_claim3.sh
