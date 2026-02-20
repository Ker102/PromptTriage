#!/bin/bash
# ═══════════════════════════════════════════════════════
# Training Entrypoint — Runs inside the compute cluster node
# ═══════════════════════════════════════════════════════
# Called by azure_ml_job.yml with arguments:
#   $1 = model_key (e.g., qwen3_8b)
#   $2 = training_data path
#   $3 = output path
#   $4 = epochs
#   $5 = lora_rank
#   $6 = learning_rate

set -e

MODEL_KEY="${1:-qwen3_8b}"
DATA_DIR="${2:-./training_data}"
OUTPUT_DIR="${3:-./outputs}"
EPOCHS="${4:-3}"
LORA_RANK="${5:-32}"
LR="${6:-0.0002}"

echo "══════════════════════════════════════════════"
echo "  Study B Training — Cluster Job"
echo "  Model:  ${MODEL_KEY}"
echo "  Data:   ${DATA_DIR}"
echo "  Output: ${OUTPUT_DIR}"
echo "  Epochs: ${EPOCHS}, LoRA rank: ${LORA_RANK}, LR: ${LR}"
echo "══════════════════════════════════════════════"

# GPU check
python -c "
import torch
print(f'PyTorch: {torch.__version__}')
print(f'CUDA: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU: {torch.cuda.get_device_name(0)}')
    print(f'VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB')
"

# Run training with overrides via environment variables
export CURRENT_MODEL="${MODEL_KEY}"
export TRAINING_DATA_DIR="${DATA_DIR}"
export OUTPUT_BASE_DIR="${OUTPUT_DIR}"
export TRAIN_EPOCHS="${EPOCHS}"
export TRAIN_LORA_RANK="${LORA_RANK}"
export TRAIN_LR="${LR}"

python study_b_cluster.py

echo "Training complete! Output saved to: ${OUTPUT_DIR}"
