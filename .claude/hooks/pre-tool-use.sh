#!/usr/bin/env sh
set -eu

if [ -x "tools/hooks/boundary_guard.py" ]; then
  python tools/hooks/boundary_guard.py --claude-pre-tool-use
fi
