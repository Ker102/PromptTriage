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

# Core training stack
install("unsloth[cu124]")
install("trl>=0.15.0")
install("datasets")
install("wandb")
install("azureml-mlflow")

# %%
import os
import json
import torch
from pathlib import Path

print(f"PyTorch: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_mem / 1e9:.1f} GB")

# %% [markdown]
# ## 2. Configuration
# 
# Select which model to train. Run this notebook once per model.

# %%
# ══════════════════════════════════════════════════════════
# SELECT MODEL — Change this per run
# ══════════════════════════════════════════════════════════
MODELS = {
    "qwen3_8b":      "Qwen/Qwen3-8B",
    "qwen3_14b":     "Qwen/Qwen3-14B",
    "qwen3_32b":     "Qwen/Qwen3-32B",
    "qwen3_30b_a3b": "Qwen/Qwen3-30B-A3B",
}

CURRENT_MODEL = "qwen3_8b"  # ← CHANGE THIS PER RUN
MODEL_ID = MODELS[CURRENT_MODEL]

# QLoRA config
QLORA_R = 16
QLORA_ALPHA = 32
QLORA_DROPOUT = 0.05

# Training config
EPOCHS = 3
BATCH_SIZE = 2
GRAD_ACCUM = 4  # Effective batch = 8
LR = 2e-4
MAX_SEQ_LEN = 8192

# Output
OUTPUT_DIR = f"./outputs/{CURRENT_MODEL}_qlora"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f"Training: {CURRENT_MODEL} ({MODEL_ID})")
print(f"QLoRA: r={QLORA_R}, alpha={QLORA_ALPHA}")
print(f"Epochs: {EPOCHS}, LR: {LR}")

# %% [markdown]
# ## 3. Load Training Data

# %%
from datasets import load_dataset

# Load from JSONL files (upload these to Azure ML Data or use local path)
DATA_DIR = Path("./training_data")

if (DATA_DIR / "train.jsonl").exists():
    train_ds = load_dataset("json", data_files=str(DATA_DIR / "train.jsonl"), split="train")
    val_ds = load_dataset("json", data_files=str(DATA_DIR / "val.jsonl"), split="train")
else:
    # Fallback: load from combined file and split
    combined_path = DATA_DIR / "combined_training_data.jsonl"
    if combined_path.exists():
        full_ds = load_dataset("json", data_files=str(combined_path), split="train")
        split = full_ds.train_test_split(test_size=0.1, seed=42)
        train_ds = split["train"]
        val_ds = split["test"]
    else:
        raise FileNotFoundError(
            f"No training data found in {DATA_DIR}. "
            "Upload train.jsonl and val.jsonl to this directory."
        )

print(f"Train: {len(train_ds)} examples")
print(f"Val:   {len(val_ds)} examples")

# Preview
sample = train_ds[0]
print(f"\nSample user prompt: {sample['messages'][1]['content'][:100]}...")
print(f"Sample response length: {len(sample['messages'][2]['content'])} chars")

# %% [markdown]
# ## 4. Load Model with Unsloth

# %%
from unsloth import FastLanguageModel

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=MODEL_ID,
    max_seq_length=MAX_SEQ_LEN,
    load_in_4bit=True,
    dtype=None,  # Auto-detect (bfloat16 on A100)
)

# Apply QLoRA adapters
model = FastLanguageModel.get_peft_model(
    model,
    r=QLORA_R,
    lora_alpha=QLORA_ALPHA,
    lora_dropout=QLORA_DROPOUT,
    target_modules=[
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ],
    bias="none",
    use_gradient_checkpointing="unsloth",
    random_state=42,
)

# Disable thinking mode for Qwen3
tokenizer.chat_template = tokenizer.chat_template.replace(
    "{{- '<think>\\n' }}", "{{- '' }}"
).replace(
    "{{- '</think>\\n\\n' }}", "{{- '' }}"
)

print(f"\nTrainable params: {model.print_trainable_parameters()}")

# %% [markdown]
# ## 5. Training

# %%
from trl import SFTTrainer, SFTConfig

training_args = SFTConfig(
    output_dir=OUTPUT_DIR,
    num_train_epochs=EPOCHS,
    per_device_train_batch_size=BATCH_SIZE,
    gradient_accumulation_steps=GRAD_ACCUM,
    learning_rate=LR,
    lr_scheduler_type="cosine",
    warmup_ratio=0.1,
    weight_decay=0.01,
    bf16=True,
    logging_steps=5,
    eval_strategy="epoch",
    save_strategy="epoch",
    save_total_limit=2,
    load_best_model_at_end=True,
    metric_for_best_model="eval_loss",
    report_to="none",  # Set to "wandb" or "mlflow" if configured
    max_seq_length=MAX_SEQ_LEN,
    dataset_text_field="",  # We use the formatting function
    packing=False,
)

def formatting_func(examples):
    """Format ChatML messages for SFT training."""
    texts = []
    for msgs in examples["messages"]:
        text = tokenizer.apply_chat_template(
            msgs, tokenize=False, add_generation_prompt=False
        )
        texts.append(text)
    return texts

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    args=training_args,
    train_dataset=train_ds,
    eval_dataset=val_ds,
    formatting_func=formatting_func,
)

print("Starting training...")
result = trainer.train()

print(f"\nTraining complete!")
print(f"  Train loss: {result.training_loss:.4f}")
print(f"  Train time: {result.metrics['train_runtime']:.0f}s")

# %% [markdown]
# ## 6. Evaluate on Validation Set

# %%
eval_results = trainer.evaluate()
print(f"Validation loss: {eval_results['eval_loss']:.4f}")

# Save eval results
with open(f"{OUTPUT_DIR}/eval_results.json", "w") as f:
    json.dump(eval_results, f, indent=2)

# %% [markdown]
# ## 7. Save Adapter

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
    "qlora_r": QLORA_R,
    "qlora_alpha": QLORA_ALPHA,
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
# ## 8. (Optional) Merge & Export GGUF
# 
# For local testing with Ollama. Skip if only using vLLM on Azure.

# %%
EXPORT_GGUF = False  # Set True if you want GGUF export

if EXPORT_GGUF:
    merged_path = f"{OUTPUT_DIR}/merged_16bit"
    model.save_pretrained_merged(merged_path, tokenizer, save_method="merged_16bit")
    print(f"Merged model saved to: {merged_path}")

    # Export GGUF Q4_K_M
    gguf_path = f"{OUTPUT_DIR}/gguf"
    model.save_pretrained_gguf(gguf_path, tokenizer, quantization_method="q4_k_m")
    print(f"GGUF saved to: {gguf_path}")

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
