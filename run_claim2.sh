#!/usr/bin/env bash
# Claim #2: zero-shot engines reach up to 70.9% (protocol mean 68.8%). No GPU needed.
# Fetches the evaluation artifact (companion repo) automatically and runs the
# checks from the committed run of record. One command, no manual steps.
set -euo pipefail
cd "$(dirname "$0")"
[ -d benchmark ] || git clone -q ${ZEROLINC_BENCHMARK_REPO:-https://github.com/CristhianKapelinski/zerolinc-benchmark} benchmark
cd benchmark && uv sync -q --extra dev && ./run_claim2.sh
