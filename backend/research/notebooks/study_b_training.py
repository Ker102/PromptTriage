# %% [markdown]
# # Study B Part 1: QLoRA Fine-Tuning
#
# Fine-tunes Qwen3 models for the Dense vs MoE breaking point analysis.
#
# **Hardware**: Azure ML `Standard_NC24ads_A100_v4` (A100 80GB)
# **Framework**: Unsloth + TRL (SFTTrainer)
# **Training Data**: 155 pairs (139 train / 16 val)
#
# ## Models
# | Round | Dense | MoE |
# |-------|-------|-----|
# | 1 | Qwen3-8B | Qwen3-30B-A3B |
# | 2 | Qwen3-14B | Qwen3-30B-A3B |
# | 3 | Qwen3-32B | Qwen3-30B-A3B |

# %% [markdown]
# ## 1. Environment Setup

# %%
import subprocess, sys

def install(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", pkg])

# Fix Azure ML environment first
install("packaging>=20.0")

# Core training stack
install("unsloth")
install("trl>=0.15.0")
install("datasets")

# %%
import os
import json
import torch
from pathlib import Path

print(f"PyTorch: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

# %% [markdown]
# ## 2. Configuration
#
# Select which model to train. Run this notebook once per model.

# %%
# ══════════════════════════════════════════════════════════
# SELECT MODEL — Change this per run
# ══════════════════════════════════════════════════════════
MODELS = {
    "qwen3_8b":      "unsloth/Qwen3-8B",
    "qwen3_14b":     "unsloth/Qwen3-14B",
    "qwen3_32b":     "unsloth/Qwen3-32B",
    "qwen3_30b_a3b": "unsloth/Qwen3-30B-A3B",
}

CURRENT_MODEL = "qwen3_8b"  # ← CHANGE THIS PER RUN
MODEL_ID = MODELS[CURRENT_MODEL]

# LoRA config (following Unsloth recommended patterns)
LORA_RANK = 32        # Suggested: 8, 16, 32, 64, 128
MAX_SEQ_LEN = 8192

# Training config
EPOCHS = 3
BATCH_SIZE = 2
GRAD_ACCUM = 4  # Effective batch = 8
LR = 2e-4

# Output
OUTPUT_DIR = f"./outputs/{CURRENT_MODEL}_qlora"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f"Training: {CURRENT_MODEL} ({MODEL_ID})")
print(f"LoRA: r={LORA_RANK}, alpha={LORA_RANK * 2}")
print(f"Epochs: {EPOCHS}, LR: {LR}")

# %% [markdown]
# ## 3. Load Training Data

# %%
from datasets import load_dataset

# Load from JSONL files
DATA_DIR = Path("./training_data")

if (DATA_DIR / "train.jsonl").exists():
    train_ds = load_dataset("json", data_files=str(DATA_DIR / "train.jsonl"), split="train")
    val_ds = load_dataset("json", data_files=str(DATA_DIR / "val.jsonl"), split="train")
else:
    combined_path = DATA_DIR / "combined_training.jsonl"
    if combined_path.exists():
        full_ds = load_dataset("json", data_files=str(combined_path), split="train")
        split = full_ds.train_test_split(test_size=0.1, seed=42)
        train_ds = split["train"]
        val_ds = split["test"]
    else:
        raise FileNotFoundError(
            f"No training data found in {DATA_DIR}. "
            "Create symlink: ln -s ../training_data ./training_data"
        )

print(f"Train: {len(train_ds)} examples")
print(f"Val:   {len(val_ds)} examples")

# Preview
sample = train_ds[0]
print(f"\nSample keys: {list(sample.keys())}")
if "messages" in sample:
    print(f"Sample user prompt: {sample['messages'][1]['content'][:100]}...")
    print(f"Sample response length: {len(sample['messages'][2]['content'])} chars")

# %% [markdown]
# ## 4. Load Model with Unsloth
#
# Using Unsloth's FastLanguageModel with recommended parameters from
# official Qwen3 notebooks.

# %%
from unsloth import FastLanguageModel

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=MODEL_ID,
    max_seq_length=MAX_SEQ_LEN,
    load_in_4bit=True,            # 4-bit for QLoRA
    fast_inference=True,           # Enable vLLM fast inference
    max_lora_rank=LORA_RANK,
    gpu_memory_utilization=0.8,    # Reduce if OOM
)

# Apply LoRA adapters (following Unsloth Qwen3 notebook pattern)
model = FastLanguageModel.get_peft_model(
    model,
    r=LORA_RANK,
    target_modules=[
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ],
    lora_alpha=LORA_RANK * 2,             # *2 speeds up training (Unsloth recommendation)
    use_gradient_checkpointing="unsloth",  # Reduces memory usage
    random_state=3407,
)

# %% [markdown]
# ## 5. Prepare Dataset
#
# SFTTrainer expects `{"messages": [...]}` format for chat data,
# or `{"text": "..."}` for pre-formatted text. Our data uses the
# messages format.

# %%
# Check data format and prepare accordingly
sample = train_ds[0]
if "messages" in sample:
    # Data is already in messages format — SFTTrainer handles this natively
    print("✅ Data in 'messages' format — SFTTrainer will apply chat template")
    DATASET_TEXT_FIELD = None  # SFTTrainer auto-detects messages format
elif "text" in sample:
    print("✅ Data in 'text' format")
    DATASET_TEXT_FIELD = "text"
else:
    # Convert messages to text field
    print("⚠️ Converting to text format...")
    def format_to_text(example):
        text = tokenizer.apply_chat_template(
            example["messages"], tokenize=False, add_generation_prompt=False
        )
        return {"text": text}
    train_ds = train_ds.map(format_to_text)
    val_ds = val_ds.map(format_to_text)
    DATASET_TEXT_FIELD = "text"

# %% [markdown]
# ## 6. Training

# %%
from trl import SFTTrainer, SFTConfig

sft_config = SFTConfig(
    output_dir=OUTPUT_DIR,
    num_train_epochs=EPOCHS,
    per_device_train_batch_size=BATCH_SIZE,
    gradient_accumulation_steps=GRAD_ACCUM,
    learning_rate=LR,
    lr_scheduler_type="linear",
    warmup_steps=5,
    weight_decay=0.01,
    optim="adamw_8bit",
    logging_steps=5,
    eval_strategy="epoch",
    save_strategy="epoch",
    save_total_limit=2,
    load_best_model_at_end=True,
    metric_for_best_model="eval_loss",
    report_to="none",
    max_seq_length=MAX_SEQ_LEN,
    seed=3407,
)

# Add dataset_text_field only if we converted to text format
if DATASET_TEXT_FIELD:
    sft_config.dataset_text_field = DATASET_TEXT_FIELD

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    args=sft_config,
    train_dataset=train_ds,
    eval_dataset=val_ds,
)

print("Starting training...")
result = trainer.train()

print(f"\nTraining complete!")
print(f"  Train loss: {result.training_loss:.4f}")
print(f"  Train time: {result.metrics['train_runtime']:.0f}s")

# %% [markdown]
# ## 7. Evaluate on Validation Set

# %%
eval_results = trainer.evaluate()
print(f"Validation loss: {eval_results['eval_loss']:.4f}")

with open(f"{OUTPUT_DIR}/eval_results.json", "w") as f:
    json.dump(eval_results, f, indent=2)

# %% [markdown]
# ## 8. Save Adapter

# %%
# Save LoRA adapter (small, ~50-200MB)
adapter_path = f"{OUTPUT_DIR}/adapter"
model.save_pretrained(adapter_path)
tokenizer.save_pretrained(adapter_path)
print(f"Adapter saved to: {adapter_path}")

# Save training metadata
metadata = {
    "model": CURRENT_MODEL,
    "model_id": MODEL_ID,
    "lora_rank": LORA_RANK,
    "lora_alpha": LORA_RANK * 2,
    "epochs": EPOCHS,
    "lr": LR,
    "train_size": len(train_ds),
    "val_size": len(val_ds),
    "eval_loss": eval_results["eval_loss"],
    "train_loss": result.training_loss,
}
with open(f"{OUTPUT_DIR}/training_metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)

print(f"\nMetadata: {json.dumps(metadata, indent=2)}")

# %% [markdown]
# ## 9. Quick Generation Test

# %%
FastLanguageModel.for_inference(model)

test_input = [
    {"role": "system", "content": "You are an expert system prompt engineer."},
    {"role": "user", "content": "Build a Python debugging assistant\nTarget vendor: anthropic"},
]

inputs = tokenizer.apply_chat_template(
    test_input, tokenize=True, add_generation_prompt=True, return_tensors="pt"
).to(model.device)

with torch.no_grad():
    outputs = model.generate(
        inputs, max_new_tokens=2048, temperature=0.7, do_sample=True
    )

response = tokenizer.decode(outputs[0][inputs.shape[-1]:], skip_special_tokens=True)
print(f"Generated ({len(response)} chars):\n")
print(response[:500] + "..." if len(response) > 500 else response)

# %%
print(f"\n{'='*60}")
print(f"TRAINING COMPLETE: {CURRENT_MODEL}")
print(f"  Adapter: {adapter_path}")
print(f"  Eval loss: {eval_results['eval_loss']:.4f}")
print(f"{'='*60}")
print(f"\nNext: Run study_b_benchmark.py to evaluate this model")
