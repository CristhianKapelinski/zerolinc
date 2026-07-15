#!/usr/bin/env bash
# Claim #1 (main): the instance-memory engine reaches 90.8% mean test accuracy.
# Fetches the evaluation artifact (companion repo) automatically and runs the
# 5-seed protocol live. One command, no manual steps.
set -euo pipefail
cd "$(dirname "$0")"
[ -d benchmark ] || git clone -q ${ZEROLINC_BENCHMARK_REPO:-https://github.com/CristhianKapelinski/zerolinc-benchmark} benchmark
cd benchmark && uv sync -q --extra dev && ./run_claim1.sh
