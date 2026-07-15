#!/usr/bin/env bash
# Claim #3: the default zero-shot engine costs seconds and under 3 Wh.
# Fetches the evaluation artifact (companion repo) automatically and runs the
# cost check (live if a GPU is present). One command, no manual steps.
set -euo pipefail
cd "$(dirname "$0")"
[ -d benchmark ] || git clone -q https://github.com/CristhianKapelinski/zerolinc-benchmark benchmark
cd benchmark && uv sync -q --extra dev && ./run_claim3.sh
