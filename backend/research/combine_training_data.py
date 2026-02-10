"""Combine corpus-direct and distillation pairs into a single training file.

This produces:
  - combined_training.jsonl (all 155 pairs, shuffled)
  - train.jsonl  (90% — ~140 pairs)
  - val.jsonl    (10% — ~15 pairs)

NOTE: These files are for Qwen3 fine-tuning ONLY.
      They are NOT for the RAG pipeline or Pinecone.
"""

import json
import os
import random

random.seed(42)

DATA_DIR = os.path.join(os.path.dirname(__file__), "training_data")
CORPUS_FILE = os.path.join(DATA_DIR, "corpus_direct_pairs.jsonl")
DISTIL_FILE = os.path.join(DATA_DIR, "distillation_pairs.jsonl")

OUTPUT_COMBINED = os.path.join(DATA_DIR, "combined_training.jsonl")
OUTPUT_TRAIN = os.path.join(DATA_DIR, "train.jsonl")
OUTPUT_VAL = os.path.join(DATA_DIR, "val.jsonl")


def load_jsonl(path: str) -> list[dict]:
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records


def save_jsonl(records: list[dict], path: str):
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def validate_record(record: dict, idx: int, source: str) -> bool:
    """Basic validation of a training record."""
    msgs = record.get("messages", [])
    if len(msgs) != 3:
        print(f"  ⚠ {source}[{idx}]: Expected 3 messages, got {len(msgs)}")
        return False
    roles = [m["role"] for m in msgs]
    if roles != ["system", "user", "assistant"]:
        print(f"  ⚠ {source}[{idx}]: Bad roles: {roles}")
        return False
    # Check assistant response is meaningful
    assistant_len = len(msgs[2]["content"])
    if assistant_len < 100:
        print(f"  ⚠ {source}[{idx}]: Response too short ({assistant_len} chars)")
        return False
    return True


def main():
    print("=" * 60)
    print("  COMBINE TRAINING DATA FOR QWEN3 FINE-TUNING")
    print("  (Training only — NOT for RAG pipeline)")
    print("=" * 60)

    # Load both sources
    corpus = load_jsonl(CORPUS_FILE)
    distil = load_jsonl(DISTIL_FILE)
    print(f"\n📦 Corpus direct pairs:   {len(corpus)}")
    print(f"📦 Distillation pairs:    {len(distil)}")

    # Validate
    print("\n🔍 Validating records...")
    valid_corpus = [r for i, r in enumerate(corpus) if validate_record(r, i, "corpus")]
    valid_distil = [r for i, r in enumerate(distil) if validate_record(r, i, "distil")]
    print(f"  ✅ Valid corpus:  {len(valid_corpus)}/{len(corpus)}")
    print(f"  ✅ Valid distil:  {len(valid_distil)}/{len(distil)}")

    # Tag source for traceability
    for r in valid_corpus:
        r["_source"] = "corpus_direct"
    for r in valid_distil:
        r["_source"] = "distillation"

    # Combine and shuffle
    combined = valid_corpus + valid_distil
    random.shuffle(combined)
    print(f"\n📊 Combined total:  {len(combined)} pairs")

    # Split train/val (90/10)
    split_idx = int(len(combined) * 0.9)
    train = combined[:split_idx]
    val = combined[split_idx:]
    print(f"  🏋️ Train split:  {len(train)} pairs")
    print(f"  🧪 Val split:    {len(val)} pairs")

    # Show vendor distribution
    vendors = {"anthropic": 0, "openai": 0, "google": 0}
    for r in combined:
        user_msg = r["messages"][1]["content"].lower()
        for v in vendors:
            if v in user_msg:
                vendors[v] += 1
    print(f"\n📈 Vendor distribution: {vendors}")

    # Show source distribution
    sources = {}
    for r in combined:
        s = r.get("_source", "unknown")
        sources[s] = sources.get(s, 0) + 1
    print(f"📈 Source distribution: {sources}")

    # Save files (strip _source tag before saving train/val)
    save_jsonl(combined, OUTPUT_COMBINED)
    print(f"\n💾 Saved: {OUTPUT_COMBINED}")

    # For train/val, remove the _source metadata
    for r in train:
        r.pop("_source", None)
    for r in val:
        r.pop("_source", None)

    save_jsonl(train, OUTPUT_TRAIN)
    save_jsonl(val, OUTPUT_VAL)
    print(f"💾 Saved: {OUTPUT_TRAIN}")
    print(f"💾 Saved: {OUTPUT_VAL}")

    # Summary stats
    total_chars = sum(len(r["messages"][2]["content"]) for r in combined)
    avg_chars = total_chars / len(combined) if combined else 0
    print(f"\n📊 Total assistant chars:     {total_chars:,}")
    print(f"📊 Avg chars per response:   {avg_chars:,.0f}")
    print(f"\n✅ Ready for Qwen3 fine-tuning!")
    print(f"   Upload train.jsonl to Colab notebook")


if __name__ == "__main__":
    main()
