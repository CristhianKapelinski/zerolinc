#!/usr/bin/env bash
# Claim #1 (main): the instance-memory engine reaches 90.8% mean test accuracy.
# Fetches the evaluation artifact (companion repo) automatically and runs the
# 5-seed protocol live. One command, no manual steps.
set -euo pipefail
cd "$(dirname "$0")"
# The evaluation run of record lives in the companion repository, pinned to the exact
# commit this artifact was evaluated at: a later change there cannot alter what you
# reproduce here.
BENCH_REPO="${ZEROLINC_BENCHMARK_REPO:-https://gitlab.com/cristhianavila.aluno/zerolinc-benchmark}"
BENCH_COMMIT="${ZEROLINC_BENCHMARK_COMMIT:-37ef42fd73a3685482e40d63e647abf44769dd6d}"

for t in git uv; do
  command -v "$t" >/dev/null 2>&1 && continue
  echo "missing required tool: $t" >&2
  if [ "$t" = uv ]; then
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
    echo "  it installs into ~/.local/bin, which the CURRENT shell picks up only" >&2
    echo '  after: export PATH="$HOME/.local/bin:$PATH"' >&2
  else
    # git is a package on every distribution, but the manager is not always apt.
    if   command -v apt-get >/dev/null 2>&1; then echo "  sudo apt-get update && sudo apt-get install -y git" >&2
    elif command -v dnf     >/dev/null 2>&1; then echo "  sudo dnf install -y git" >&2
    elif command -v pacman  >/dev/null 2>&1; then echo "  sudo pacman -Sy --needed git" >&2
    elif command -v zypper  >/dev/null 2>&1; then echo "  sudo zypper install -y git" >&2
    else echo "  install git with your distribution's package manager" >&2; fi
  fi
  exit 1
done

if [ ! -d benchmark ]; then
  git clone -q "$BENCH_REPO" benchmark
  git -C benchmark checkout -q "$BENCH_COMMIT"
fi
cd benchmark && uv sync -q --extra dev && ./run_claim1.sh
