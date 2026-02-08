#!/usr/bin/env python3
"""
Enhanced System Prompts Ingestion Script (google.genai SDK)

Ingests prompts from system-prompts-reference/ with vendor-specific namespaces:
- system-prompts (all prompts)
- system-prompts-anthropic
- system-prompts-openai
- system-prompts-google
- system-prompts-misc (xAI, Perplexity, Proton, Misc)
"""

import os
import sys
import json
import time
import argparse
import re
from pathlib import Path
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pinecone import Pinecone

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()

# Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "prompttriage-prompts")
EMBEDDING_MODEL = "models/gemini-embedding-001"
EMBEDDING_DIMENSIONS = 768  # Must match Pinecone index
LABELING_MODEL = "gemini-2.0-flash"

# Vendor mapping
VENDOR_MAP = {
    "anthropic": "system-prompts-anthropic",
    "openai": "system-prompts-openai",
    "google": "system-prompts-google",
    "xai": "system-prompts-misc",
    "perplexity": "system-prompts-misc",
    "proton": "system-prompts-misc",
    "misc": "system-prompts-misc",
}

# Labeling prompt
LABELING_PROMPT = """Analyze this system prompt and provide structured metadata.

<prompt_content>
{content}
</prompt_content>

<source_info>
Vendor: {vendor}
Filename: {filename}
Size: {size_kb} KB
</source_info>

Respond with ONLY a valid JSON object (no markdown, no code fences):
{{
  "model": "extracted model name (e.g., claude-opus-4.6, gpt-5.2, gemini-3-pro) or 'unknown'",
  "category": "base|tool|personality|thinking|memory|voice|code|workspace|chrome|excel",
  "techniques": ["list of techniques like: xml-tags, few-shot, chain-of-thought, structured-output, role-play, guardrails, tool-definitions"],
  "quality": "high|medium|low",
  "summary": "One-sentence summary of what this prompt does",
  "key_sections": ["list of sections detected like: identity, capabilities, rules, thinking, output_format, tools, safety"]
}}

Be precise. Extract the model name from content if present."""


# Initialize genai client
client = None


def init_clients():
    """Initialize Gemini and Pinecone clients."""
    global client
    client = genai.Client(api_key=GOOGLE_API_KEY)
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX_NAME)
    return index


def get_embedding(text: str) -> list[float]:
    """Generate embedding using Gemini embedding-001 (768-dim for Pinecone compat)."""
    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text[:10000],
        config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIMENSIONS)
    )
    return result.embeddings[0].values


def extract_model_from_filename(filename: str) -> str:
    """Extract model name from filename."""
    patterns = [
        r"claude[-_]?(opus|sonnet|haiku)?[-_]?(\d+\.?\d*)",
        r"gpt[-_]?(\d+\.?\d*)",
        r"gemini[-_]?(\d+\.?\d*)",
        r"o(\d+)[-_]?(mini|high)?",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename.lower())
        if match:
            return match.group(0).replace("_", "-")
    
    return filename.replace(".md", "").replace(".txt", "").replace(".xml", "")


def label_prompt(content: str, vendor: str, filename: str, size_kb: float) -> Optional[dict]:
    """Use Gemini to analyze and label a prompt."""
    try:
        response = client.models.generate_content(
            model=LABELING_MODEL,
            contents=LABELING_PROMPT.format(
                content=content[:15000],
                vendor=vendor,
                filename=filename,
                size_kb=round(size_kb, 1)
            ),
            config=types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json"
            )
        )
        
        result = json.loads(response.text)
        return result
    except Exception as e:
        print(f"  [WARN] Labeling failed: {e}")
        return None


def find_prompt_files(repo_path: Path) -> list[tuple[Path, str]]:
    """Find all prompt files in the repository."""
    prompt_files = []
    
    for ext in ["*.txt", "*.md", "*.xml", "*.js"]:
        for file_path in repo_path.rglob(ext):
            # Skip meta files
            if file_path.name.lower() in ["license.md", "readme.md", ".gitignore"]:
                continue
            if any(part.startswith(".") for part in file_path.parts):
                continue
            # Skip 'old' directories
            if "old" in [p.lower() for p in file_path.parts]:
                continue
            # Skip API subdirectory (OpenAI/API has duplicates)
            relative = file_path.relative_to(repo_path)
            if len(relative.parts) > 2 and relative.parts[1].lower() == "api":
                continue
                
            vendor = relative.parts[0].lower() if len(relative.parts) > 1 else "misc"
            prompt_files.append((file_path, vendor))
    
    # Also pick up extensionless files (some prompts like claude-opus-4.5 have no extension)
    for file_path in repo_path.rglob("*"):
        if file_path.is_file() and not file_path.suffix:
            if file_path.name.lower() in [".gitignore"]:
                continue
            if any(part.startswith(".") for part in file_path.parts):
                continue
            if "old" in [p.lower() for p in file_path.parts]:
                continue
            relative = file_path.relative_to(repo_path)
            vendor = relative.parts[0].lower() if len(relative.parts) > 1 else "misc"
            # Only if it's large enough to be a prompt
            try:
                size = file_path.stat().st_size
                if size > 500:
                    prompt_files.append((file_path, vendor))
            except OSError:
                pass
    
    # Deduplicate
    seen = set()
    unique = []
    for fp, v in prompt_files:
        if fp not in seen:
            seen.add(fp)
            unique.append((fp, v))
    
    return unique


def process_and_ingest(
    repo_path: Path,
    index,
    batch_size: int = 10,
    delay: float = 1.0,
    dry_run: bool = False,
    vendor_filter: Optional[str] = None
):
    """Process all prompts, label them, and ingest to Pinecone."""
    
    prompt_files = find_prompt_files(repo_path)
    print(f"[FILES] Found {len(prompt_files)} prompt files")
    
    if vendor_filter:
        prompt_files = [(f, v) for f, v in prompt_files if v == vendor_filter.lower()]
        print(f"[FILTER] Filtered to {len(prompt_files)} files for vendor '{vendor_filter}'")
    
    # Group by vendor for stats
    vendor_counts = {}
    for _, vendor in prompt_files:
        vendor_counts[vendor] = vendor_counts.get(vendor, 0) + 1
    print(f"[STATS] By vendor: {vendor_counts}")
    
    all_batch = []
    vendor_batches = {}
    
    processed = 0
    failed = 0
    
    for file_path, vendor in prompt_files:
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            size_kb = len(content.encode('utf-8')) / 1024
            
            if len(content.strip()) < 100:
                print(f"  [SKIP] {file_path.name} (too short: {len(content)} chars)")
                continue
            
            print(f"\n[{vendor.upper()}] {file_path.name} ({size_kb:.1f} KB)")
            
            # Label with Gemini
            labels = label_prompt(content, vendor, file_path.name, size_kb)
            
            if not labels:
                labels = {
                    "model": extract_model_from_filename(file_path.name),
                    "category": "base",
                    "techniques": [],
                    "quality": "unknown",
                    "summary": f"System prompt from {vendor}",
                    "key_sections": []
                }
            
            print(f"  Model: {labels.get('model', 'unknown')}")
            print(f"  Category: {labels.get('category')}")
            print(f"  Summary: {labels.get('summary', 'N/A')[:80]}")
            
            if dry_run:
                ns = VENDOR_MAP.get(vendor, 'system-prompts-misc')
                print(f"  [DRY RUN] Would ingest to: system-prompts + {ns}")
                processed += 1
                continue
            
            # Generate embedding
            embedding = get_embedding(content)
            
            # Create unique ID
            doc_id = f"sp-{vendor}-{file_path.stem.lower().replace(' ', '-')[:50]}"
            
            # Flatten list fields to strings for Pinecone metadata
            techniques = labels.get("techniques", [])
            key_sections = labels.get("key_sections", [])
            
            metadata = {
                "content": content[:8000],
                "vendor": vendor,
                "filename": file_path.name,
                "size_kb": round(size_kb, 1),
                "modality": "text",
                "dataset": "system-prompts-reference",
                "ingested_at": datetime.now().isoformat(),
                "model": labels.get("model", "unknown"),
                "category": labels.get("category", "base"),
                "techniques": ", ".join(techniques) if isinstance(techniques, list) else str(techniques),
                "quality": labels.get("quality", "unknown"),
                "summary": labels.get("summary", ""),
                "key_sections": ", ".join(key_sections) if isinstance(key_sections, list) else str(key_sections),
            }
            
            vector = {
                "id": doc_id,
                "values": embedding,
                "metadata": metadata
            }
            
            all_batch.append(vector)
            
            vendor_ns = VENDOR_MAP.get(vendor, "system-prompts-misc")
            if vendor_ns not in vendor_batches:
                vendor_batches[vendor_ns] = []
            vendor_batches[vendor_ns].append(vector)
            
            processed += 1
            
            if len(all_batch) >= batch_size:
                print(f"\n[UPSERT] Batch of {len(all_batch)} vectors...")
                index.upsert(vectors=all_batch, namespace="system-prompts")
                
                for ns, vectors in vendor_batches.items():
                    if vectors:
                        index.upsert(vectors=vectors, namespace=ns)
                        print(f"  -> {ns}: {len(vectors)} vectors")
                
                all_batch = []
                vendor_batches = {}
                time.sleep(delay)
            
            time.sleep(0.3)  # Rate limit
            
        except Exception as e:
            print(f"  [ERROR] {e}")
            failed += 1
    
    if all_batch and not dry_run:
        print(f"\n[UPSERT] Final batch of {len(all_batch)} vectors...")
        index.upsert(vectors=all_batch, namespace="system-prompts")
        
        for ns, vectors in vendor_batches.items():
            if vectors:
                index.upsert(vectors=vectors, namespace=ns)
                print(f"  -> {ns}: {len(vectors)} vectors")
    
    print(f"\n[DONE] Processed: {processed}, Failed: {failed}")
    
    if not dry_run:
        stats = index.describe_index_stats()
        print(f"\n[INDEX STATS]")
        print(f"  Total vectors: {stats.get('total_vector_count', 'unknown')}")
        if 'namespaces' in stats:
            for ns, ns_stats in stats['namespaces'].items():
                print(f"  {ns}: {ns_stats.get('vector_count', 0)} vectors")


def main():
    parser = argparse.ArgumentParser(description="Ingest system prompts with vendor namespaces")
    parser.add_argument(
        "--repo-path",
        type=str,
        default="../../system-prompts-reference",
        help="Path to the system-prompts-reference repository (relative to this script)"
    )
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--dry-run", action="store_true", help="Label only, no Pinecone upsert")
    parser.add_argument("--vendor", type=str, help="Only process a specific vendor")
    
    args = parser.parse_args()
    
    # Resolve path relative to this script's location
    script_dir = Path(__file__).parent
    repo_path = (script_dir / args.repo_path).resolve()
    
    if not repo_path.exists():
        print(f"[ERROR] Repository not found: {repo_path}")
        print(f"  Expected at: {repo_path}")
        print(f"  Script dir: {script_dir}")
        return
    
    print(f"=== System Prompts Reference Ingestion ===")
    print(f"Source: {repo_path}")
    print(f"Labeling model: {LABELING_MODEL}")
    print(f"Embedding model: {EMBEDDING_MODEL}")
    print(f"Index: {PINECONE_INDEX_NAME}")
    print(f"Dry run: {args.dry_run}")
    print(f"Namespaces: system-prompts, system-prompts-anthropic, system-prompts-openai, system-prompts-google, system-prompts-misc")
    print("")
    
    index = init_clients()
    process_and_ingest(
        repo_path,
        index,
        batch_size=args.batch_size,
        delay=args.delay,
        dry_run=args.dry_run,
        vendor_filter=args.vendor
    )


if __name__ == "__main__":
    main()
