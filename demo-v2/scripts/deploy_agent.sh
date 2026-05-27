#!/usr/bin/env bash
# deploy_agent.sh — Deploy a hosted agent to Azure AI Foundry
#
# Usage:
#   ./scripts/deploy_agent.sh <agent_type> <model_id>
#
# Examples:
#   ./scripts/deploy_agent.sh zava-next o4-mini
#   ./scripts/deploy_agent.sh zava gpt-4.1
#   ./scripts/deploy_agent.sh zava-next gpt-4.1-mini
#
# Prerequisites:
#   - azd provisioned project (run from demo-v2/deploy/ first time)
#   - Azure CLI logged in
#   - TOOL_URL env vars set (or defaults used)
#
# The script will:
#   1. Generate a concrete manifest from the template
#   2. Run azd ai agent init + azd deploy
#   3. Grant the required role to the agent's instance identity
#   4. Wait for role propagation and test the agent

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DEPLOY_DIR="$REPO_ROOT/deploy"

# --- Parse arguments ---
if [ $# -lt 2 ]; then
    echo "Usage: $0 <agent_type> <model_id>"
    echo ""
    echo "Agent types: zava, zava-next"
    echo "Model IDs:   o4-mini, gpt-4.1, gpt-4.1-mini, gpt-4.1-nano, gpt-5.4, gpt-5.4-mini"
    echo ""
    echo "Examples:"
    echo "  $0 zava-next o4-mini"
    echo "  $0 zava gpt-4.1"
    exit 1
fi

AGENT_TYPE="$1"
MODEL_ID="$2"

# --- Validate agent type ---
if [[ "$AGENT_TYPE" != "zava" && "$AGENT_TYPE" != "zava-next" ]]; then
    echo "Error: agent_type must be 'zava' or 'zava-next'"
    exit 1
fi

# --- Set tool URL based on agent type ---
if [ "$AGENT_TYPE" == "zava-next" ]; then
    TOOL_URL="${ZAVA_NEXT_TOOL_URL:-https://zava-next-tools-omkarm.azurewebsites.net}"
else
    TOOL_URL="${ZAVA_TOOL_URL:-https://zava-rft-tools-omkarm.azurewebsites.net}"
fi

# --- Model SKU/version mapping ---
# Each model needs a specific SKU and version for deployment
get_model_config() {
    local model="$1"
    case "$model" in
        o4-mini)
            MODEL_SKU="Standard"
            MODEL_VERSION="2025-04-16"
            MODEL_CAPACITY=50
            ;;
        gpt-4.1)
            MODEL_SKU="DataZoneStandard"
            MODEL_VERSION="2025-04-14"
            MODEL_CAPACITY=50
            ;;
        gpt-4.1-mini)
            MODEL_SKU="Standard"
            MODEL_VERSION="2025-04-14"
            MODEL_CAPACITY=50
            ;;
        gpt-4.1-nano)
            MODEL_SKU="GlobalStandard"
            MODEL_VERSION="2025-04-14"
            MODEL_CAPACITY=50
            ;;
        gpt-5.4)
            MODEL_SKU="GlobalStandard"
            MODEL_VERSION="2026-03-05"
            MODEL_CAPACITY=50
            ;;
        gpt-5.4-mini)
            MODEL_SKU="GlobalStandard"
            MODEL_VERSION="2026-03-17"
            MODEL_CAPACITY=50
            ;;
        *)
            echo "Error: Unknown model '$model'. Add it to the model config in this script."
            exit 1
            ;;
    esac
}

get_model_config "$MODEL_ID"

# --- Paths ---
AGENT_DIR="$REPO_ROOT/agents/$AGENT_TYPE"
TEMPLATE="$AGENT_DIR/agent.manifest.yaml"

# --- Sanitize model ID for agent naming (dots not allowed) ---
SAFE_MODEL_ID=$(echo "$MODEL_ID" | tr '.' '-')
SERVICE_NAME="$AGENT_TYPE-$SAFE_MODEL_ID"
SRC_DIR="$DEPLOY_DIR/src/$SERVICE_NAME"

echo "============================================"
echo " Deploying: $SERVICE_NAME"
echo " Model:     $MODEL_ID"
echo " Tool URL:  $TOOL_URL"
echo " Source:    $SRC_DIR"
echo "============================================"
echo ""

# --- Update source in deploy/src/ (this is what azd actually deploys) ---
echo "[1/5] Updating source files..."
mkdir -p "$SRC_DIR"

# Copy latest agent code
cp "$AGENT_DIR/main.py" "$SRC_DIR/"
cp "$AGENT_DIR/Dockerfile" "$SRC_DIR/"
cp "$AGENT_DIR/requirements.txt" "$SRC_DIR/"

# Generate manifest from template
sed -e "s|{{MODEL_ID}}|$MODEL_ID|g" \
    -e "s|{{TOOL_URL}}|$TOOL_URL|g" \
    "$TEMPLATE" | \
    sed -e "s|name: $AGENT_TYPE-$MODEL_ID|name: $SERVICE_NAME|g" \
    > "$SRC_DIR/agent.manifest.yaml"

echo "  Updated: $SRC_DIR/main.py"
echo "  Manifest: $SRC_DIR/agent.manifest.yaml"
echo ""

# --- Ensure model is deployed ---
echo "[2/5] Ensuring model deployment exists..."
cd "$DEPLOY_DIR"

# Get resource group and account name from azd env
RG=$(azd env get-value AZURE_RESOURCE_GROUP)
ACCOUNT_NAME=$(azd env get-value AZURE_AI_ACCOUNT_NAME)

# Check if model deployment already exists
if az cognitiveservices account deployment show \
    --name "$ACCOUNT_NAME" -g "$RG" \
    --deployment-name "$MODEL_ID" &>/dev/null; then
    echo "  Model '$MODEL_ID' already deployed ✓"
else
    echo "  Deploying model '$MODEL_ID' (SKU: $MODEL_SKU, version: $MODEL_VERSION, capacity: $MODEL_CAPACITY)..."
    az cognitiveservices account deployment create \
        --name "$ACCOUNT_NAME" \
        --resource-group "$RG" \
        --deployment-name "$MODEL_ID" \
        --model-name "$MODEL_ID" \
        --model-version "$MODEL_VERSION" \
        --model-format OpenAI \
        --sku-capacity "$MODEL_CAPACITY" \
        --sku-name "$MODEL_SKU" \
        --only-show-errors
    echo "  Model '$MODEL_ID' deployed ✓"
fi
echo ""

# --- Deploy agent with azd ---
echo "[3/5] Deploying agent container..."
cd "$DEPLOY_DIR"

# Deploy only this service (no init needed — azure.yaml already has it)
azd deploy "$SERVICE_NAME" --no-prompt

echo ""
echo "[4/5] Granting role to agent instance identity..."
echo "  (Note: Role may already exist from a previous agent in the same project)"

# Get instance identity
INSTANCE_ID=$(azd ai agent show | grep "Instance Identity Client ID" | awk '{print $NF}')
if [ -z "$INSTANCE_ID" ]; then
    echo "Error: Could not get Instance Identity Client ID"
    echo "Run 'azd ai agent show' manually to debug"
    exit 1
fi

# Get account scope
ACCOUNT_ID=$(azd env get-value AZURE_AI_PROJECT_ID | sed 's|/projects/.*||')
if [ -z "$ACCOUNT_ID" ]; then
    echo "Error: Could not get account ID from AZURE_AI_PROJECT_ID"
    exit 1
fi

echo "  Instance ID: $INSTANCE_ID"
echo "  Account scope: $ACCOUNT_ID"

# Grant Azure AI/Foundry User role (idempotent — safe to re-run)
az role assignment create \
    --assignee-object-id "$INSTANCE_ID" \
    --assignee-principal-type ServicePrincipal \
    --role "53ca6127-db72-4b80-b1b0-d745d6d5456d" \
    --scope "$ACCOUNT_ID" \
    --only-show-errors 2>/dev/null || echo "  (Role already exists — OK)"

echo ""
echo "[5/5] Deployment complete!"
echo ""
echo "  Agent name: $SERVICE_NAME"
echo "  Model:      $MODEL_ID"
echo ""
echo "  ⚠️  Role propagation takes 3-5 minutes."
echo "  Test with:"
echo "    cd $DEPLOY_DIR && azd ai agent invoke --message \"Hello, what can you help me with?\""
echo ""
echo "============================================"
