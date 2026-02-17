#!/bin/bash
# ═══════════════════════════════════════════════════════
# Study B Setup — Run ONCE on a fresh Azure ML instance
# ═══════════════════════════════════════════════════════
# Usage:
#   cd ~/cloudfiles/code/Users/<user>/prompttriage/backend/research/notebooks
#   chmod +x setup_azure_ml.sh && ./setup_azure_ml.sh

set -e

echo "══════════════════════════════════════════════"
echo "  Study B: Azure ML Environment Setup"
echo "══════════════════════════════════════════════"

# 1. Fix packaging (known Azure ML issue)
echo "[1/7] Fixing packaging..."
pip install --no-cache-dir "packaging>=20.0,<26.0"

# 2. Remove TensorFlow/Keras (causes import conflicts with transformers)
#    We only use PyTorch — TF is pre-installed by Azure ML but not needed
echo "[2/7] Removing TensorFlow/Keras (not needed, causes conflicts)..."
pip uninstall -y tensorflow tf-keras keras tensorboard 2>/dev/null || true

# 3. Pin numpy to match pre-installed pandas (pandas 1.5.3 needs numpy <2)
echo "[3/7] Pinning numpy for pandas compatibility..."
pip install "numpy==1.23.5"

# 4. Install training deps
echo "[4/7] Installing training dependencies..."
pip install -r requirements.txt

# 5. Symlink training data
echo "[5/7] Linking training data..."
if [ ! -e ./training_data ]; then
    ln -s ../training_data ./training_data
    echo "  Created symlink: training_data -> ../training_data"
else
    echo "  training_data already linked"
fi

# 6. Create outputs dir
echo "[6/7] Creating outputs directory..."
mkdir -p ./outputs

# 7. Verify
echo "[7/7] Verifying..."
python -c "
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
print()
print('✅ All good! Run: python study_b_training.py')
"
