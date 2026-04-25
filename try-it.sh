#!/usr/bin/env bash
# try-it.sh — Run all Statewave demos in sequence.
# Requires: Statewave server at http://localhost:8100
#           pip install statewave-py
set -euo pipefail

STATEWAVE_URL="${STATEWAVE_URL:-http://localhost:8100}"
export STATEWAVE_URL

echo "============================================"
echo "  Statewave Demo Suite"
echo "  Server: $STATEWAVE_URL"
echo "============================================"

# Check server is reachable
if ! curl -sf "$STATEWAVE_URL/healthz" > /dev/null 2>&1; then
    echo ""
    echo "❌ Statewave server not reachable at $STATEWAVE_URL"
    echo ""
    echo "Start it with:"
    echo "  docker compose up -d    # from this directory"
    echo ""
    echo "Or see README.md for setup instructions."
    exit 1
fi

echo ""
echo "────────────────────────────────────────────"
echo "  1/3  Minimal Quickstart"
echo "────────────────────────────────────────────"
echo ""
python minimal-quickstart/quickstart.py

echo ""
echo "────────────────────────────────────────────"
echo "  2/3  Support Agent Demo"
echo "────────────────────────────────────────────"
echo ""
python support-agent-python/support_agent.py

echo ""
echo "────────────────────────────────────────────"
echo "  3/3  Coding Agent Demo"
echo "────────────────────────────────────────────"
echo ""
python coding-agent-python/coding_agent.py

echo ""
echo "============================================"
echo "  ✅ All demos completed!"
echo "============================================"
echo ""
echo "Next steps:"
echo "  - Read the code in each example directory"
echo "  - Try modifying the episodes and rerunning"
echo "  - Check the API docs at $STATEWAVE_URL/docs"
echo "  - Build your own agent with: pip install statewave-py"
