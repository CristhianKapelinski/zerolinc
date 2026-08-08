#!/usr/bin/env bash
# Minimal test: the offline unit suite, then one real zero-shot classification of the
# bundled sample tickets. Exercises the whole path a user takes, not --help.
#
# The first run downloads the default zero-shot checkpoint (~0.8 GB) from the HuggingFace
# Hub; later runs are offline. Nothing is written outside this directory.
set -euo pipefail
cd "$(dirname "$0")"

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

echo "== [1/2] unit suite (offline, no model) =="
uv run --extra dev pytest -q

echo
echo "== [2/2] classifying the bundled sample with the zero-shot engine =="
uv run zerolinc classify --input examples/tickets_sample.csv --engine zeroshot

echo
echo "MINIMAL TEST: PASSED"
