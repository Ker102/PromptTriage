# %% [markdown]
# # PromptTriage — Qwen3 QLoRA Fine-Tuning
# 
# **Study B: Can an open-source Qwen3 model match proprietary APIs**
# **for system prompt generation?**
# 
# This notebook fine-tunes two Qwen 3 models on our system prompt corpus:
# - **Qwen3-8B** (dense, fits T4 with 4-bit)
# - **Qwen3-30B-A3B** (MoE, 30B total / 3B active — fits T4 too!)
# 
# **Stack**: Unsloth + QLoRA + SFTTrainer
# **Runtime**: Google Colab (T4 GPU, ~30min per model)

# %% [markdown]
# ## 1. Install Dependencies

# %%
# Install Unsloth (2x faster fine-tuning, 70% less VRAM)
!pip install -q unsloth
!pip install -q trl datasets

# %% [markdown]
# ## 2. Configuration
# 
# Change `MODEL_CHOICE` to switch between the two models.

# %%
import os, json, torch

# ============================================================
# MODEL CHOICE — Toggle between the two research models
# ============================================================
MODEL_CHOICE = "8B"  # Options: "8B" or "30B_MoE"

MODEL_CONFIG = {
    "8B": {
        "name": "unsloth/Qwen3-8B-unsloth-bnb-4bit",
        "max_seq_length": 8192,       # Qwen3 supports up to 128K
        "lora_rank": 64,
        "gpu_memory_utilization": 0.6,
        "output_dir": "qwen3_8b_qlora",
    },
    "30B_MoE": {
        "name": "unsloth/Qwen3-30B-A3B-unsloth-bnb-4bit",
        "max_seq_length": 4096,       # Shorter for MoE memory
        "lora_rank": 32,              # Lower rank for MoE
        "gpu_memory_utilization": 0.7,
        "output_dir": "qwen3_30b_a3b_qlora",
    },
}

cfg = MODEL_CONFIG[MODEL_CHOICE]
print(f"🎯 Model: {cfg['name']}")
print(f"📐 LoRA Rank: {cfg['lora_rank']}")
print(f"📏 Max Seq Length: {cfg['max_seq_length']}")

# %% [markdown]
# ## 3. Load Model with 4-bit Quantization

# %%
from unsloth import FastLanguageModel, is_bfloat16_supported

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=cfg["name"],
    max_seq_length=cfg["max_seq_length"],
    load_in_4bit=True,
    fast_inference=True,
    max_lora_rank=cfg["lora_rank"],
    gpu_memory_utilization=cfg["gpu_memory_utilization"],
)

print(f"✅ Model loaded: {cfg['name']}")
print(f"📊 GPU Memory: {torch.cuda.memory_allocated() / 1e9:.1f} GB")

# %% [markdown]
# ## 4. Add LoRA Adapters

# %%
model = FastLanguageModel.get_peft_model(
    model,
    r=cfg["lora_rank"],
    target_modules=[
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ],
    lora_alpha=cfg["lora_rank"],
    use_gradient_checkpointing="unsloth",  # 60% less VRAM
    random_state=3407,
)

# Count trainable parameters
trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
total = sum(p.numel() for p in model.parameters())
print(f"🔧 Trainable: {trainable:,} / {total:,} ({100*trainable/total:.2f}%)")

# %% [markdown]
# ## 5. Load Training Data
#
# Upload your JSONL training data from the research pipeline.
# Expected format (ChatML):
# ```json
# {"messages": [
#     {"role": "system", "content": "You are a system prompt engineer..."},
#     {"role": "user", "content": "Build me a Python debugging assistant\nTarget vendor: anthropic"},
#     {"role": "assistant", "content": "<identity>You are a Python debugging assistant...</identity>..."}
# ]}
# ```

# %%
from google.colab import files
from datasets import Dataset

# Option A: Upload from local machine
print("📤 Upload your training JSONL file:")
uploaded = files.upload()
data_file = list(uploaded.keys())[0]

# Option B: If on Google Drive (uncomment below)
# from google.colab import drive
# drive.mount('/content/drive')
# data_file = '/content/drive/MyDrive/prompttriage/corpus_direct_pairs.jsonl'

# Load the JSONL data
records = []
with open(data_file, "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            records.append(json.loads(line))

print(f"📊 Loaded {len(records)} training examples")

# %% [markdown]
# ## 6. Format Dataset for SFTTrainer

# %%
def format_training_example(example):
    """Convert ChatML messages to Qwen3 chat template format."""
    messages = example["messages"]
    
    # Build text using tokenizer's chat template
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=False,
        enable_thinking=False,  # Non-thinking mode for training
    )
    return {"text": text}


# Create HuggingFace Dataset
dataset = Dataset.from_list(records)
dataset = dataset.map(format_training_example)

# Quick sanity check
print(f"\n📋 Dataset size: {len(dataset)}")
print(f"📏 Avg text length: {sum(len(x['text']) for x in dataset) / len(dataset):.0f} chars")
print(f"\n--- Sample (first 500 chars) ---")
print(dataset[0]["text"][:500])

# %% [markdown]
# ## 7. Train with SFTTrainer

# %%
from trl import SFTTrainer, SFTConfig

# Training hyperparameters tuned for system prompt generation
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    args=SFTConfig(
        dataset_text_field="text",
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,    # Effective batch size = 4
        warmup_steps=10,
        num_train_epochs=3,               # 3 epochs for small datasets
        learning_rate=2e-4,               # Standard for QLoRA
        logging_steps=5,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="cosine",       # Cosine > linear for fine-tuning
        seed=3407,
        report_to="none",
        max_seq_length=cfg["max_seq_length"],
        fp16=not is_bfloat16_supported(),
        bf16=is_bfloat16_supported(),
        output_dir=cfg["output_dir"],
        save_strategy="epoch",
    ),
)

print("🚀 Starting training...")
trainer_stats = trainer.train()

# Training summary
print(f"\n{'='*50}")
print(f"✅ Training Complete!")
print(f"⏱️  Total time: {trainer_stats.metrics['train_runtime']:.0f}s")
print(f"📉 Final loss: {trainer_stats.metrics['train_loss']:.4f}")
print(f"🔄 Steps: {trainer_stats.metrics['train_steps']}")

# %% [markdown]
# ## 8. Test the Fine-Tuned Model

# %%
# Test with a sample prompt from our test suite
test_prompts = [
    {
        "role": "system",
        "content": "You are a system prompt engineer. Generate production-quality system prompts matching the target vendor's conventions."
    },
    {
        "role": "user",
        "content": "Build me a Python debugging assistant that helps developers find and fix bugs.\nTarget vendor: anthropic"
    },
]

# Generate with thinking disabled (production mode)
FastLanguageModel.for_inference(model)

input_text = tokenizer.apply_chat_template(
    test_prompts,
    tokenize=False,
    add_generation_prompt=True,
    enable_thinking=False,
)

inputs = tokenizer(input_text, return_tensors="pt").to("cuda")

# Generate
with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_new_tokens=4096,
        temperature=0.7,
        do_sample=True,
    )

# Decode only the generated portion
response = tokenizer.decode(
    outputs[0][inputs["input_ids"].shape[1]:],
    skip_special_tokens=True
)

print("🎯 Generated System Prompt:\n")
print(response[:2000])
print(f"\n📏 Total words: {len(response.split())}")

# %% [markdown]
# ## 9. Test with Thinking Mode (Optional)
# 
# Qwen 3 can also do step-by-step reasoning before generating.

# %%
# Generate WITH thinking enabled
input_text_think = tokenizer.apply_chat_template(
    test_prompts,
    tokenize=False,
    add_generation_prompt=True,
    enable_thinking=True,  # Enable reasoning traces
)

inputs_think = tokenizer(input_text_think, return_tensors="pt").to("cuda")

with torch.no_grad():
    outputs_think = model.generate(
        **inputs_think,
        max_new_tokens=8192,  # More tokens for thinking
        temperature=0.6,
        do_sample=True,
    )

response_think = tokenizer.decode(
    outputs_think[0][inputs_think["input_ids"].shape[1]:],
    skip_special_tokens=True
)

# Split thinking from output
if "<think>" in response_think and "</think>" in response_think:
    thinking = response_think.split("<think>")[1].split("</think>")[0]
    output = response_think.split("</think>")[1]
    print("🧠 Thinking Process:\n")
    print(thinking[:1000])
    print(f"\n🎯 Generated Prompt:\n")
    print(output[:1000])
else:
    print(response_think[:2000])

# %% [markdown]
# ## 10. Save Model

# %%
# Save LoRA adapters (small, ~50-200 MB)
adapter_path = f"/content/{cfg['output_dir']}_adapters"
model.save_pretrained(adapter_path)
tokenizer.save_pretrained(adapter_path)
print(f"💾 LoRA adapters saved to: {adapter_path}")

# %% [markdown]
# ### Save to Google Drive (recommended)

# %%
from google.colab import drive
drive.mount('/content/drive', force_remount=False)

drive_path = f"/content/drive/MyDrive/prompttriage/{cfg['output_dir']}"
os.makedirs(drive_path, exist_ok=True)

model.save_pretrained(drive_path)
tokenizer.save_pretrained(drive_path)
print(f"✅ Saved to Drive: {drive_path}")

# %% [markdown]
# ### Export to GGUF for Ollama (optional)

# %%
# Export to 4-bit GGUF (for running via Ollama on local machine)
gguf_path = f"/content/{cfg['output_dir']}_gguf"

model.save_pretrained_gguf(
    gguf_path,
    tokenizer,
    quantization_method="q4_k_m",  # Good quality-to-size balance
)
print(f"📦 GGUF saved to: {gguf_path}")

# Download the GGUF file
from google.colab import files
gguf_file = [f for f in os.listdir(gguf_path) if f.endswith('.gguf')][0]
files.download(f"{gguf_path}/{gguf_file}")

# %% [markdown]
# ## 11. Upload to Hugging Face Hub (optional)

# %%
# HF_TOKEN = "hf_..."  # Your Hugging Face token
# model.push_to_hub_merged(
#     f"your-username/{cfg['output_dir']}",
#     tokenizer,
#     save_method="merged_16bit",
#     token=HF_TOKEN,
# )

# %% [markdown]
# ## 12. Quick Benchmark (Run Both Models)
# 
# After training both models, compare their outputs on the same test prompts.

# %%
# Run this cell after training BOTH models (8B and 30B)
benchmark_prompts = [
    ("Build a Python code reviewer", "anthropic"),
    ("Create a customer support bot", "openai"),
    ("Design a content writing assistant", "google"),
]

print(f"\n{'='*60}")
print(f"Quick Benchmark: {cfg['output_dir']}")
print(f"{'='*60}")

FastLanguageModel.for_inference(model)

for prompt, vendor in benchmark_prompts:
    messages = [
        {"role": "system", "content": "You are a system prompt engineer."},
        {"role": "user", "content": f"{prompt}\nTarget vendor: {vendor}"},
    ]
    
    input_text = tokenizer.apply_chat_template(
        messages, tokenize=False,
        add_generation_prompt=True, enable_thinking=False,
    )
    inputs = tokenizer(input_text, return_tensors="pt").to("cuda")
    
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=2048, temperature=0.7, do_sample=True)
    
    response = tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
    word_count = len(response.split())
    
    print(f"\n📝 {prompt} ({vendor}): {word_count} words")
    print(f"   Preview: {response[:200]}...")
