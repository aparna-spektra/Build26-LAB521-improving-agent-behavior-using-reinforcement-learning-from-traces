#!/usr/bin/env bash
# deploy_all.sh — Deploy all agent variants (both agent types × all models)
#
# Usage:
#   ./scripts/deploy_all.sh              # Deploy everything
#   ./scripts/deploy_all.sh zava-next    # Deploy only zava-next variants
#   ./scripts/deploy_all.sh zava         # Deploy only zava variants
#
# This deploys agents sequentially. Each deployment takes ~2-3 minutes.
# Total time for all 12 agents: ~25-35 minutes.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Models to deploy
MODELS=(
    "o4-mini"
    "gpt-4.1"
    "gpt-4.1-mini"
    "gpt-4.1-nano"
    "gpt-5.4"
    "gpt-5.4-mini"
)

# Determine which agent types to deploy
FILTER="${1:-all}"

if [[ "$FILTER" == "all" ]]; then
    AGENT_TYPES=("zava-next" "zava")
elif [[ "$FILTER" == "zava-next" || "$FILTER" == "zava" ]]; then
    AGENT_TYPES=("$FILTER")
else
    echo "Usage: $0 [all|zava|zava-next]"
    exit 1
fi

echo "============================================"
echo " Batch Agent Deployment"
echo " Agent types: ${AGENT_TYPES[*]}"
echo " Models: ${MODELS[*]}"
echo "============================================"
echo ""

TOTAL=0
SUCCEEDED=0
FAILED=0

for agent_type in "${AGENT_TYPES[@]}"; do
    for model in "${MODELS[@]}"; do
        TOTAL=$((TOTAL + 1))
        echo ""
        echo ">>> [$TOTAL] Deploying $agent_type-$model ..."
        echo ""
        
        if "$SCRIPT_DIR/deploy_agent.sh" "$agent_type" "$model"; then
            SUCCEEDED=$((SUCCEEDED + 1))
            echo ">>> ✅ $agent_type-$model deployed successfully"
        else
            FAILED=$((FAILED + 1))
            echo ">>> ❌ $agent_type-$model FAILED"
        fi
        
        echo ""
        echo "---"
    done
done

echo ""
echo "============================================"
echo " Deployment Summary"
echo "  Total:     $TOTAL"
echo "  Succeeded: $SUCCEEDED"
echo "  Failed:    $FAILED"
echo "============================================"

if [ $FAILED -gt 0 ]; then
    exit 1
fi
