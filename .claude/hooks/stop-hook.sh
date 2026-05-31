#!/usr/bin/env sh
set -eu

if [ -f "frontier.yaml" ]; then
  python tools/verify.py --smoke
fi
