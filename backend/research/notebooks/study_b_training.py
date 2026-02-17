# %% [markdown]
# # Study B Part 1: QLoRA Fine-Tuning
#
# Fine-tunes Qwen3 models for the Dense vs MoE breaking point analysis.
#
# **Hardware**: Azure ML `Standard_NC24ads_A100_v4` (A100 80GB)
# **Framework**: Unsloth + TRL (SFTTrainer)
# **Training Data**: 155 pairs (139 train / 16 val)
#
# ## Prerequisites
# Run setup ONCE before first use:
# ```bash
# chmod +x setup_azure_ml.sh && ./setup_azure_ml.sh
# ```
#
# ## Models
# | Round | Dense | MoE |
# |-------|-------|-----|
# | 1 | Qwen3-8B | Qwen3-30B-A3B |
# | 2 | Qwen3-14B | Qwen3-30B-A3B |
# | 3 | Qwen3-32B | Qwen3-30B-A3B |

# %% [markdown]
# ## 1. Verify Environment

# %%
import os
import json
import torch
from pathlib import Path

print(f"PyTorch: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    props = torch.cuda.get_device_properties(0)
    print(f"VRAM: {props.total_memory / 1e9:.1f} GB")
else:
    raise RuntimeError("No CUDA GPU detected. This script requires a GPU.")

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

# LoRA config (following Unsloth Qwen3 notebook patterns)
LORA_RANK = 32        # Suggested: 8, 16, 32, 64, 128
MAX_SEQ_LEN = 8192

# Training config
EPOCHS = 3
BATCH_SIZE = 2
GRAD_ACCUM = 4  # Effective batch = BATCH_SIZE * GRAD_ACCUM = 8
LR = 2e-4

# Output
OUTPUT_DIR = f"./outputs/{CURRENT_MODEL}_qlora"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f"Training: {CURRENT_MODEL} ({MODEL_ID})")
print(f"LoRA: r={LORA_RANK}, alpha={LORA_RANK * 2}")
print(f"Epochs: {EPOCHS}, Effective batch: {BATCH_SIZE * GRAD_ACCUM}, LR: {LR}")

# %% [markdown]
# ## 3. Load Training Data

# %%
from datasets import load_dataset

DATA_DIR = Path("./training_data")

if not DATA_DIR.exists():
    # Try relative path from notebook location
    alt = Path(__file__).parent / "training_data" if "__file__" in dir() else None
    if alt and alt.exists():
        DATA_DIR = alt
    else:
        raise FileNotFoundError(
            f"Training data not found at {DATA_DIR}.\n"
            "Run: ln -s ../training_data ./training_data"
        )

if (DATA_DIR / "train.jsonl").exists():
    train_ds = load_dataset("json", data_files=str(DATA_DIR / "train.jsonl"), split="train")
    val_ds = load_dataset("json", data_files=str(DATA_DIR / "val.jsonl"), split="train")
elif (DATA_DIR / "combined_training.jsonl").exists():
    full_ds = load_dataset("json", data_files=str(DATA_DIR / "combined_training.jsonl"), split="train")
    split = full_ds.train_test_split(test_size=0.1, seed=42)
    train_ds, val_ds = split["train"], split["test"]
else:
    raise FileNotFoundError(f"No .jsonl files found in {DATA_DIR}")

print(f"Train: {len(train_ds)} examples")
print(f"Val:   {len(val_ds)} examples")

# Preview first sample
sample = train_ds[0]
print(f"\nSample keys: {list(sample.keys())}")
if "messages" in sample:
    for msg in sample["messages"]:
        role = msg["role"]
        content_preview = msg["content"][:80].replace("\n", " ")
        print(f"  {role}: {content_preview}...")

# %% [markdown]
# ## 4. Load Model with Unsloth

# %%
from unsloth import FastLanguageModel

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=MODEL_ID,
    max_seq_length=MAX_SEQ_LEN,
    load_in_4bit=True,            # 4-bit quantization for QLoRA
    fast_inference=True,           # Enable vLLM fast inference
    max_lora_rank=LORA_RANK,
    gpu_memory_utilization=0.8,    # Reduce to 0.6 if OOM
)

print(f"✅ Model loaded: {MODEL_ID}")

# %% [markdown]
# ## 5. Apply LoRA Adapters

# %%
model = FastLanguageModel.get_peft_model(
    model,
    r=LORA_RANK,
    target_modules=[
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ],
    lora_alpha=LORA_RANK * 2,             # Unsloth recommends alpha = 2*rank
    use_gradient_checkpointing="unsloth",  # Unsloth optimized checkpointing
    random_state=3407,
)

# Count trainable params
total = sum(p.numel() for p in model.parameters())
trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
print(f"Total params: {total:,}")
print(f"Trainable:    {trainable:,} ({100 * trainable / total:.2f}%)")

# %% [markdown]
# ## 6. Prepare Dataset
#
# Our JSONL data uses `{"messages": [...]}` format.
# SFTTrainer natively handles this format — it applies the model's
# chat template automatically. We just need to convert to text
# using `apply_chat_template` if the data has a "messages" column.

# %%
def format_chat(example):
    """Convert messages list to formatted text using the model's chat template."""
    text = tokenizer.apply_chat_template(
        example["messages"],
        tokenize=False,
        add_generation_prompt=False,
    )
    return {"text": text}

# Always convert to text format for maximum compatibility
print("Formatting dataset with chat template...")
train_ds = train_ds.map(format_chat, remove_columns=train_ds.column_names)
val_ds = val_ds.map(format_chat, remove_columns=val_ds.column_names)

print(f"✅ Formatted. Sample length: {len(train_ds[0]['text'])} chars")
print(f"   Preview: {train_ds[0]['text'][:200]}...")

# %% [markdown]
# ## 7. Training

# %%
from trl import SFTTrainer, SFTConfig

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=train_ds,
    eval_dataset=val_ds,
    args=SFTConfig(
        dataset_text_field="text",
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
    ),
)

print(f"Starting training ({EPOCHS} epochs)...")
result = trainer.train()

print(f"\n✅ Training complete!")
print(f"  Train loss: {result.training_loss:.4f}")
print(f"  Runtime:    {result.metrics['train_runtime']:.0f}s")

# %% [markdown]
# ## 8. Evaluate

# %%
eval_results = trainer.evaluate()
print(f"Validation loss: {eval_results['eval_loss']:.4f}")

with open(f"{OUTPUT_DIR}/eval_results.json", "w") as f:
    json.dump(eval_results, f, indent=2)

# %% [markdown]
# ## 9. Save Adapter

# %%
adapter_path = f"{OUTPUT_DIR}/adapter"
model.save_pretrained(adapter_path)
tokenizer.save_pretrained(adapter_path)
print(f"✅ Adapter saved: {adapter_path}")

# Save training metadata
metadata = {
    "model": CURRENT_MODEL,
    "model_id": MODEL_ID,
    "lora_rank": LORA_RANK,
    "lora_alpha": LORA_RANK * 2,
    "epochs": EPOCHS,
    "batch_size": BATCH_SIZE * GRAD_ACCUM,
    "lr": LR,
    "train_size": len(train_ds),
    "val_size": len(val_ds),
    "eval_loss": eval_results["eval_loss"],
    "train_loss": result.training_loss,
    "train_runtime_s": result.metrics["train_runtime"],
}
with open(f"{OUTPUT_DIR}/training_metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)

print(f"\nMetadata:\n{json.dumps(metadata, indent=2)}")

# %% [markdown]
# ## 10. Quick Smoke Test

# %%
FastLanguageModel.for_inference(model)

test_messages = [
    {"role": "system", "content": "You are an expert system prompt engineer."},
    {"role": "user", "content": "Build a Python debugging assistant\nTarget vendor: anthropic"},
]

inputs = tokenizer.apply_chat_template(
    test_messages, tokenize=True, add_generation_prompt=True, return_tensors="pt"
).to(model.device)

with torch.no_grad():
    outputs = model.generate(
        input_ids=inputs,
        max_new_tokens=2048,
        temperature=0.7,
        do_sample=True,
    )

response = tokenizer.decode(outputs[0][inputs.shape[-1]:], skip_special_tokens=True)
print(f"Generated ({len(response)} chars):\n")
print(response[:500] + "..." if len(response) > 500 else response)

# %% [markdown]
# ## Done

# %%
print(f"\n{'='*60}")
print(f"TRAINING COMPLETE: {CURRENT_MODEL}")
print(f"  Adapter:   {adapter_path}")
print(f"  Eval loss:  {eval_results['eval_loss']:.4f}")
print(f"  Train loss: {result.training_loss:.4f}")
print(f"{'='*60}")
print(f"\nNext steps:")
print(f"  1. Change CURRENT_MODEL and re-run for next model")
print(f"  2. After all models trained, run study_b_benchmark.py")
