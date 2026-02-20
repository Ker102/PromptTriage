#!/bin/bash
# ═══════════════════════════════════════════════════════
# Submit Study B Training Jobs to Azure ML Compute Cluster
# ═══════════════════════════════════════════════════════
#
# Prerequisites:
#   1. Azure CLI installed: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli
#   2. ML extension: az extension add -n ml
#   3. Login: az login
#   4. Set defaults:
#      az account set --subscription <sub-id>
#      az configure --defaults group=<resource-group> workspace=<workspace>
#
# Usage:
#   # Submit single model:
#   ./submit_job.sh qwen3_8b
#
#   # Submit all 4 models:
#   ./submit_job.sh all
#
#   # Check status:
#   az ml job list --query "[?experiment_name=='prompttriage-study-b']" -o table

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Step 0: Ensure compute cluster exists ──
ensure_cluster() {
    local CLUSTER_NAME="gpu-a100"
    
    if az ml compute show --name "$CLUSTER_NAME" &>/dev/null; then
        echo "✅ Cluster '$CLUSTER_NAME' exists"
    else
        echo "Creating compute cluster '$CLUSTER_NAME'..."
        echo "  VM: Standard_NC24ads_A100_v4 (A100 80GB)"
        echo "  Min nodes: 0 (auto-scale to zero)"
        echo "  Max nodes: 1"
        az ml compute create \
            --name "$CLUSTER_NAME" \
            --type amlcompute \
            --size Standard_NC24ads_A100_v4 \
            --min-instances 0 \
            --max-instances 1 \
            --idle-time-before-scale-down 300
        echo "✅ Cluster created"
    fi
}

# ── Submit a single training job ──
submit_model() {
    local MODEL_KEY="$1"
    echo ""
    echo "═══════════════════════════════════════"
    echo "  Submitting: ${MODEL_KEY}"
    echo "═══════════════════════════════════════"
    
    az ml job create \
        --file azure_ml_job.yml \
        --set "inputs.model_key=${MODEL_KEY}" \
        --set "display_name=study-b-${MODEL_KEY}" \
        --name "study-b-${MODEL_KEY}-$(date +%Y%m%d-%H%M%S)"
    
    echo "✅ Job submitted for ${MODEL_KEY}"
}

# ── Main ──
MODEL_KEY="${1:-qwen3_8b}"

echo "══════════════════════════════════════════════"
echo "  Study B — Compute Cluster Job Submission"
echo "══════════════════════════════════════════════"

# Check az ml is available
if ! az ml -h &>/dev/null; then
    echo "❌ Azure ML CLI not found. Install with:"
    echo "   az extension add -n ml"
    exit 1
fi

# Ensure cluster exists
ensure_cluster

if [ "$MODEL_KEY" = "all" ]; then
    echo ""
    echo "Submitting ALL 4 models..."
    for m in qwen3_8b qwen3_14b qwen3_32b qwen3_30b_a3b; do
        submit_model "$m"
    done
    echo ""
    echo "═══════════════════════════════════════"
    echo "  All 4 jobs submitted!"
    echo "  Monitor: az ml job list --query \"[?experiment_name=='prompttriage-study-b']\" -o table"
    echo "═══════════════════════════════════════"
else
    submit_model "$MODEL_KEY"
    echo ""
    echo "Monitor: az ml job show --name study-b-${MODEL_KEY}-* -o table"
fi
