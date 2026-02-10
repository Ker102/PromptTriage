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
# **Runtime**: Colab Enterprise (A100 via GCP credits) or Colab Free (T4)
#
# **Training data**: 155 pairs (95 corpus-direct + 60 distillation)
# These are for fine-tuning ONLY — NOT for RAG pipeline.

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
# The data is split into train.jsonl (~139 pairs) and val.jsonl (~16 pairs).
#
# **Important**: This data is for fine-tuning ONLY, not for RAG/Pinecone.
#
# Expected format (ChatML):
# ```json
# {"messages": [
#     {"role": "system", "content": "You are a system prompt engineer..."},
#     {"role": "user", "content": "Build me a Python debugging assistant\nTarget vendor: anthropic"},
#     {"role": "assistant", "content": "<identity>You are a Python debugging assistant...</identity>..."}
# ]}
# ```

# %%
from datasets import Dataset
import glob

def load_jsonl(path: str) -> list:
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records

# ============================================================
# DATA LOADING — Choose ONE option below
# ============================================================

# Option A: Upload from local machine (Colab Free / Pro)
from google.colab import files
print("📤 Upload train.jsonl and val.jsonl:")
uploaded = files.upload()
train_file = "train.jsonl"
val_file = "val.jsonl" if "val.jsonl" in uploaded else None

# Option B: Colab Enterprise with GCS bucket (uncomment below)
# !gsutil cp gs://YOUR_BUCKET/prompttriage/train.jsonl .
# !gsutil cp gs://YOUR_BUCKET/prompttriage/val.jsonl .
# train_file = "train.jsonl"
# val_file = "val.jsonl"

# Option C: Google Drive (uncomment below)
# from google.colab import drive
# drive.mount('/content/drive')
# train_file = '/content/drive/MyDrive/prompttriage/train.jsonl'
# val_file = '/content/drive/MyDrive/prompttriage/val.jsonl'

# Load the data
train_records = load_jsonl(train_file)
val_records = load_jsonl(val_file) if val_file else []

print(f"📊 Training examples:   {len(train_records)}")
print(f"📊 Validation examples: {len(val_records)}")

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


# Create HuggingFace Datasets
train_dataset = Dataset.from_list(train_records)
train_dataset = train_dataset.map(format_training_example)

eval_dataset = None
if val_records:
    eval_dataset = Dataset.from_list(val_records)
    eval_dataset = eval_dataset.map(format_training_example)

# Quick sanity check
print(f"\n📋 Train dataset: {len(train_dataset)} examples")
print(f"📏 Avg text length: {sum(len(x['text']) for x in train_dataset) / len(train_dataset):.0f} chars")
if eval_dataset:
    print(f"📋 Val dataset:   {len(eval_dataset)} examples")
print(f"\n--- Sample (first 500 chars) ---")
print(train_dataset[0]["text"][:500])

# %% [markdown]
# ## 7. Train with SFTTrainer

# %%
from trl import SFTTrainer, SFTConfig

# Training hyperparameters tuned for system prompt generation
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
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
        # Validation evaluation
        eval_strategy="epoch" if eval_dataset else "no",
        per_device_eval_batch_size=1,
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

# %% [markdown]
# ## 13. Full Benchmark — Run 30 Test Prompts
# 
# Runs the entire test suite, saves results as JSON for local `llm_judge.py` scoring.
# **Download the JSON** and score locally:
# ```bash
# cd backend
# python -c "
# from research.llm_judge import LLMJudge
# import json
# judge = LLMJudge()
# with open('results.json') as f: data = json.load(f)
# for r in data:
#     score = judge.score(r['output'], r['vendor'], '', r['prompt'])
#     print(f'{r[\"id\"]}: {score.total}/50')
# "
# ```

# %%
import time as _time

# Full test suite from our research framework
TEST_PROMPTS = [
    # Coding × Anthropic
    {"id": "code_anth_1", "prompt": "Build a Python debugging assistant that helps developers find and fix bugs", "vendor": "anthropic", "cat": "coding"},
    {"id": "code_anth_2", "prompt": "Create a code review bot that catches security vulnerabilities and suggests fixes", "vendor": "anthropic", "cat": "coding"},
    {"id": "code_anth_3", "prompt": "Design a SQL query optimizer that explains performance improvements", "vendor": "anthropic", "cat": "coding"},
    # Coding × OpenAI
    {"id": "code_oai_1", "prompt": "Build an API documentation generator from source code", "vendor": "openai", "cat": "coding"},
    {"id": "code_oai_2", "prompt": "Create a test generation assistant for Python pytest with edge cases", "vendor": "openai", "cat": "coding"},
    {"id": "code_oai_3", "prompt": "Design a Kubernetes troubleshooting assistant", "vendor": "openai", "cat": "coding"},
    # Coding × Google
    {"id": "code_goog_1", "prompt": "Build a data pipeline debugging assistant for GCP", "vendor": "google", "cat": "coding"},
    {"id": "code_goog_2", "prompt": "Create a cloud architecture reviewer for multi-region deployments", "vendor": "google", "cat": "coding"},
    {"id": "code_goog_3", "prompt": "Design a CI/CD pipeline assistant that suggests optimizations", "vendor": "google", "cat": "coding"},
    # Business × Anthropic
    {"id": "biz_anth_1", "prompt": "Create a customer support chatbot for a SaaS product", "vendor": "anthropic", "cat": "business"},
    {"id": "biz_anth_2", "prompt": "Build a competitive analysis agent for market research", "vendor": "anthropic", "cat": "business"},
    {"id": "biz_anth_3", "prompt": "Design a legal document reviewer for GDPR compliance", "vendor": "anthropic", "cat": "business"},
    # Business × OpenAI
    {"id": "biz_oai_1", "prompt": "Build a resume screening assistant with bias mitigation", "vendor": "openai", "cat": "business"},
    {"id": "biz_oai_2", "prompt": "Create a financial planning assistant for small businesses", "vendor": "openai", "cat": "business"},
    {"id": "biz_oai_3", "prompt": "Design an HR onboarding assistant for remote teams", "vendor": "openai", "cat": "business"},
    # Business × Google
    {"id": "biz_goog_1", "prompt": "Build a meeting summarizer that extracts action items", "vendor": "google", "cat": "business"},
    {"id": "biz_goog_2", "prompt": "Create a project status reporter from Jira and GitHub", "vendor": "google", "cat": "business"},
    {"id": "biz_goog_3", "prompt": "Design a sales proposal generator from CRM data", "vendor": "google", "cat": "business"},
    # Creative × Anthropic
    {"id": "cre_anth_1", "prompt": "Build a blog content writer optimized for SEO", "vendor": "anthropic", "cat": "creative"},
    {"id": "cre_anth_2", "prompt": "Create a brand naming and trademark assistant", "vendor": "anthropic", "cat": "creative"},
    {"id": "cre_anth_3", "prompt": "Design a storytelling assistant for interactive fiction", "vendor": "anthropic", "cat": "creative"},
    # Creative × OpenAI
    {"id": "cre_oai_1", "prompt": "Build a video script writer for YouTube tutorials", "vendor": "openai", "cat": "creative"},
    {"id": "cre_oai_2", "prompt": "Create a UX copywriter for web application microcopy", "vendor": "openai", "cat": "creative"},
    {"id": "cre_oai_3", "prompt": "Design a social media content calendar generator", "vendor": "openai", "cat": "creative"},
    # Creative × Google
    {"id": "cre_goog_1", "prompt": "Build an email marketing copywriter with A/B test variants", "vendor": "google", "cat": "creative"},
    {"id": "cre_goog_2", "prompt": "Create a product description writer for e-commerce", "vendor": "google", "cat": "creative"},
    {"id": "cre_goog_3", "prompt": "Design a podcast episode planner and script generator", "vendor": "google", "cat": "creative"},
]

SYS_MSG = "You are a system prompt engineer. Generate production-quality system prompts matching the target vendor's conventions."

print(f"\n{'='*60}")
print(f"FULL BENCHMARK: {cfg['output_dir']} — {len(TEST_PROMPTS)} prompts")
print(f"{'='*60}\n")

FastLanguageModel.for_inference(model)
results = []

for i, tp in enumerate(TEST_PROMPTS):
    print(f"[{i+1}/{len(TEST_PROMPTS)}] {tp['id']}: {tp['prompt'][:50]}...")
    
    messages = [
        {"role": "system", "content": SYS_MSG},
        {"role": "user", "content": f"{tp['prompt']}\nTarget vendor: {tp['vendor']}"},
    ]
    
    input_text = tokenizer.apply_chat_template(
        messages, tokenize=False,
        add_generation_prompt=True, enable_thinking=False,
    )
    inputs = tokenizer(input_text, return_tensors="pt").to("cuda")
    
    t0 = _time.time()
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=4096, temperature=0.7, do_sample=True)
    latency_ms = int((_time.time() - t0) * 1000)
    
    response = tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
    
    results.append({
        "id": tp["id"],
        "prompt": tp["prompt"],
        "vendor": tp["vendor"],
        "category": tp["cat"],
        "output": response,
        "word_count": len(response.split()),
        "latency_ms": latency_ms,
        "model": cfg["output_dir"],
    })
    
    print(f"   → {len(response.split())} words, {latency_ms}ms")

# Save results
results_file = f"/content/{cfg['output_dir']}_benchmark_results.json"
with open(results_file, "w") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"\n{'='*60}")
print(f"✅ Benchmark complete! {len(results)} prompts processed.")
print(f"📊 Avg words: {sum(r['word_count'] for r in results) / len(results):.0f}")
print(f"⏱️  Avg latency: {sum(r['latency_ms'] for r in results) / len(results):.0f}ms")
print(f"💾 Saved to: {results_file}")

# %% [markdown]
# ### Download Results

# %%
# Download the benchmark results JSON
from google.colab import files
files.download(results_file)
print(f"📥 Downloading {results_file}...")
print("Score locally: python -c 'from research.llm_judge import LLMJudge; ...'")

