#!/bin/bash
# ═══════════════════════════════════════════════════════
# Study B Setup — Run ONCE on a fresh Azure ML instance
# ═══════════════════════════════════════════════════════
#
# Creates an ISOLATED conda environment to avoid conflicts
# with Azure ML's pre-installed packages.
#
# Usage:
#   cd ~/cloudfiles/code/Users/<user>/prompttriage/backend/research/notebooks
#   chmod +x setup_azure_ml.sh && ./setup_azure_ml.sh
#
# After setup, always activate before running:
#   conda activate unsloth
#   python study_b_training.py

set -e

echo "══════════════════════════════════════════════"
echo "  Study B: Isolated Environment Setup"
echo "══════════════════════════════════════════════"

ENV_NAME="unsloth"

# 1. Check if env already exists
if conda info --envs | grep -q "^${ENV_NAME} "; then
    echo "[1/4] Environment '${ENV_NAME}' already exists."
    echo "  To recreate: conda env remove -n ${ENV_NAME} && ./setup_azure_ml.sh"
else
    echo "[1/4] Creating isolated conda environment '${ENV_NAME}'..."
    echo "  This installs Python 3.11 + PyTorch + Unsloth + TRL (5-10 min)"
    conda env create -f environment.yml
fi

# 2. Symlink training data
echo "[2/4] Linking training data..."
if [ ! -e ./training_data ]; then
    ln -s ../training_data ./training_data
    echo "  Created symlink: training_data -> ../training_data"
else
    echo "  training_data already linked"
fi

# 3. Create outputs dir
echo "[3/4] Creating outputs directory..."
mkdir -p ./outputs

# 4. Verify (must run inside the conda env)
echo "[4/4] Verifying installation..."
conda run -n ${ENV_NAME} python -c "
import torch
print(f'PyTorch: {torch.__version__}')
print(f'CUDA: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU: {torch.cuda.get_device_name(0)}')
    print(f'VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB')
from unsloth import FastLanguageModel
print('Unsloth: OK')
from trl import SFTTrainer, SFTConfig
print('TRL: OK')
from datasets import load_dataset
print('Datasets: OK')
import numpy; print(f'NumPy: {numpy.__version__}')
import pandas; print(f'Pandas: {pandas.__version__}')
print()
print('✅ All good!')
"

echo ""
echo "══════════════════════════════════════════════"
echo "  Setup complete! Run training with:"
echo ""
echo "  conda activate ${ENV_NAME}"
echo "  python study_b_training.py"
echo "══════════════════════════════════════════════"
