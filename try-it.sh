#!/usr/bin/env bash
# try-it.sh — Run all Python Statewave demos in sequence.
# Requires: Statewave server at http://localhost:8100
#           pip install statewave-py
set -euo pipefail

STATEWAVE_URL="${STATEWAVE_URL:-http://localhost:8100}"
export STATEWAVE_URL

echo "Statewave demo suite — server: $STATEWAVE_URL"

if ! curl -sf "$STATEWAVE_URL/healthz" > /dev/null 2>&1; then
    echo "Statewave server not reachable at $STATEWAVE_URL"
    echo "Start it with:  docker compose up -d"
    exit 1
fi

heading() { echo; echo "----- $1 -----"; }

heading "1/4  Minimal Quickstart"
python minimal-quickstart/quickstart.py

heading "2/4  Support Agent"
python support-agent-python/support_agent.py

heading "3/4  Coding Agent"
python coding-agent-python/coding_agent.py

heading "4/4  Context Quality Eval"
python -m pytest eval-support-agent/test_support_context.py -q

echo
echo "All demos completed."
echo "Next: read each example's README, modify the seed episodes, rerun."
