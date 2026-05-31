#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/../.."

if [[ "${1:-}" == "resume" ]]; then
  shift
  exec python tools/frontier/ralph_driver.py resume "$@"
fi

exec python tools/frontier/ralph_driver.py run "$@"
