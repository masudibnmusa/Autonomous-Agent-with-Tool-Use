#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

if [ -d ".venv" ]; then
  source .venv/bin/activate
fi

if [ $# -eq 0 ]; then
  echo "Usage: ./run.sh \"your task here\""
  exit 1
fi

python -m app.main --goal "$*"