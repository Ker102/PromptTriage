"""
Study B Cluster Training — Headless training optimized for Azure ML compute clusters.

Reads config from environment variables (set by train_entrypoint.sh):
  CURRENT_MODEL, TRAINING_DATA_DIR, OUTPUT_BASE_DIR,
  TRAIN_EPOCHS, TRAIN_LORA_RANK, TRAIN_LR
"""
import os
import json
import torch
from pathlib import Path

# ── Config from environment ──
MODELS = {
    "qwen3_8b":      "unsloth/Qwen3-8B",
    "qwen3_14b":     "unsloth/Qwen3-14B",
    "qwen3_32b":     "unsloth/Qwen3-32B",
    "qwen3_30b_a3b": "unsloth/Qwen3-30B-A3B",
}

CURRENT_MODEL = os.environ.get("CURRENT_MODEL", "qwen3_8b")
MODEL_ID = MODELS[CURRENT_MODEL]
DATA_DIR = Path(os.environ.get("TRAINING_DATA_DIR", "./training_data"))
OUTPUT_DIR = os.environ.get("OUTPUT_BASE_DIR", f"./outputs/{CURRENT_MODEL}_qlora")
EPOCHS = int(os.environ.get("TRAIN_EPOCHS", "3"))
LORA_RANK = int(os.environ.get("TRAIN_LORA_RANK", "32"))
LR = float(os.environ.get("TRAIN_LR", "0.0002"))
MAX_SEQ_LEN = 8192
BATCH_SIZE = 2
GRAD_ACCUM = 4

os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f"PyTorch: {torch.__version__}")
print(f"CUDA: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
else:
    raise RuntimeError("No GPU available!")

print(f"\nTraining: {CURRENT_MODEL} ({MODEL_ID})")
print(f"LoRA: r={LORA_RANK}, alpha={LORA_RANK * 2}")
print(f"Epochs: {EPOCHS}, Effective batch: {BATCH_SIZE * GRAD_ACCUM}, LR: {LR}")

# ── Load Data ──
from datasets import load_dataset

if (DATA_DIR / "train.jsonl").exists():
    train_ds = load_dataset("json", data_files=str(DATA_DIR / "train.jsonl"), split="train")
    val_ds = load_dataset("json", data_files=str(DATA_DIR / "val.jsonl"), split="train")
elif (DATA_DIR / "combined_training.jsonl").exists():
    full_ds = load_dataset("json", data_files=str(DATA_DIR / "combined_training.jsonl"), split="train")
    split = full_ds.train_test_split(test_size=0.1, seed=42)
    train_ds, val_ds = split["train"], split["test"]
else:
    raise FileNotFoundError(f"No training data in {DATA_DIR}")

print(f"Train: {len(train_ds)} | Val: {len(val_ds)}")

# ── Load Model ──
from unsloth import FastLanguageModel

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=MODEL_ID,
    max_seq_length=MAX_SEQ_LEN,
    load_in_4bit=True,
    fast_inference=False,  # vLLM not installed; only affects inference speed, not training
    max_lora_rank=LORA_RANK,
)

model = FastLanguageModel.get_peft_model(
    model,
    r=LORA_RANK,
    target_modules=[
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ],
    lora_alpha=LORA_RANK * 2,
    use_gradient_checkpointing="unsloth",
    random_state=3407,
)

total = sum(p.numel() for p in model.parameters())
trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
print(f"Params: {total:,} total, {trainable:,} trainable ({100*trainable/total:.2f}%)")

# ── Format Dataset ──
def format_chat(example):
    text = tokenizer.apply_chat_template(
        example["messages"], tokenize=False, add_generation_prompt=False
    )
    return {"text": text}

train_ds = train_ds.map(format_chat, remove_columns=train_ds.column_names)
val_ds = val_ds.map(format_chat, remove_columns=val_ds.column_names)
print(f"Formatted. Sample: {len(train_ds[0]['text'])} chars")

# ── Train ──
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

print(f"\nStarting training ({EPOCHS} epochs)...")
result = trainer.train()
print(f"✅ Train loss: {result.training_loss:.4f} | Runtime: {result.metrics['train_runtime']:.0f}s")

# ── Evaluate ──
eval_results = trainer.evaluate()
print(f"✅ Val loss: {eval_results['eval_loss']:.4f}")

# ── Save ──
adapter_path = f"{OUTPUT_DIR}/adapter"
model.save_pretrained(adapter_path)
tokenizer.save_pretrained(adapter_path)

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

with open(f"{OUTPUT_DIR}/eval_results.json", "w") as f:
    json.dump(eval_results, f, indent=2)

# ── Smoke Test ──
FastLanguageModel.for_inference(model)
test_msgs = [
    {"role": "system", "content": "You are an expert system prompt engineer."},
    {"role": "user", "content": "Build a Python debugging assistant\nTarget vendor: anthropic"},
]
inputs = tokenizer.apply_chat_template(
    test_msgs, tokenize=True, add_generation_prompt=True, return_tensors="pt"
).to(model.device)
with torch.no_grad():
    outputs = model.generate(input_ids=inputs, max_new_tokens=512, temperature=0.7, do_sample=True)
response = tokenizer.decode(outputs[0][inputs.shape[-1]:], skip_special_tokens=True)
print(f"\nSmoke test ({len(response)} chars): {response[:200]}...")

print(f"\n{'='*60}")
print(f"COMPLETE: {CURRENT_MODEL}")
print(f"  Adapter: {adapter_path}")
print(f"  Eval loss: {eval_results['eval_loss']:.4f}")
print(f"{'='*60}")
