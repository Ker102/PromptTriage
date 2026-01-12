#!/usr/bin/env python3
"""
LLM-Assisted System Prompt Labeling and Ingestion Script

Uses Gemini 3 Pro to analyze and label system prompts from the 
system-prompts-and-models-of-ai-tools repository, then ingests them to Pinecone.
"""

import os
import json
import time
import argparse
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import google.generativeai as genai
from pinecone import Pinecone

# Load environment variables
load_dotenv()

# Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "prompttriage-prompts")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "models/embedding-001")

# Gemini model for labeling
LABELING_MODEL = "gemini-3-pro-preview"

# Category taxonomy
LABELING_PROMPT = """Analyze this system prompt and provide structured metadata.

<prompt_content>
{content}
</prompt_content>

<source_info>
Source: {source}
Filename: {filename}
</source_info>

Respond with a JSON object containing:
{{
  "category": "one of: system-prompt, agentic, code-gen, reasoning, ui-gen, docs, chat, tool-use",
  "subcategories": ["list", "of", "relevant", "subcategories"],
  "techniques": ["xml-tags", "few-shot", "chain-of-thought", "structured-output", "role-play", "guardrails", "tool-definitions", "etc"],
  "modality": "text",
  "quality": "high | medium | low (based on completeness and clarity)",
  "summary": "One-sentence summary of what this prompt does",
  "key_patterns": ["Notable patterns or structures used in this prompt"]
}}

Be precise and thorough. Extract all relevant techniques and patterns."""


def init_clients():
    """Initialize Gemini and Pinecone clients."""
    genai.configure(api_key=GOOGLE_API_KEY)
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX_NAME)
    return index


def get_embedding(text: str) -> list[float]:
    """Generate embedding using Gemini."""
    result = genai.embed_content(
        model=EMBEDDING_MODEL,
        content=text,
        task_type="retrieval_document"
    )
    return result['embedding']


def label_prompt(content: str, source: str, filename: str) -> Optional[dict]:
    """Use Gemini to analyze and label a prompt."""
    model = genai.GenerativeModel(LABELING_MODEL)
    
    try:
        response = model.generate_content(
            LABELING_PROMPT.format(
                content=content[:15000],  # Truncate very long prompts
                source=source,
                filename=filename
            ),
            generation_config=genai.GenerationConfig(
                temperature=0.2,
                response_mime_type="application/json"
            )
        )
        
        # Parse JSON response
        result = json.loads(response.text)
        return result
    except Exception as e:
        print(f"  ⚠️ Labeling failed: {e}")
        return None


def find_prompt_files(repo_path: Path) -> list[tuple[Path, str]]:
    """Find all prompt files in the repository."""
    prompt_files = []
    
    for ext in ["*.txt", "*.md"]:
        for file_path in repo_path.rglob(ext):
            # Skip LICENSE and README
            if file_path.name.lower() in ["license.md", "readme.md"]:
                continue
            # Skip hidden and git directories
            if any(part.startswith(".") for part in file_path.parts):
                continue
                
            # Determine source from directory structure
            relative = file_path.relative_to(repo_path)
            source = relative.parts[0] if len(relative.parts) > 1 else "unknown"
            
            prompt_files.append((file_path, source))
    
    return prompt_files


def process_and_ingest(
    repo_path: Path,
    index,
    batch_size: int = 10,
    delay: float = 1.0,
    dry_run: bool = False
):
    """Process all prompts, label them, and ingest to Pinecone."""
    
    prompt_files = find_prompt_files(repo_path)
    print(f"📁 Found {len(prompt_files)} prompt files")
    
    batch = []
    processed = 0
    failed = 0
    
    for file_path, source in prompt_files:
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            
            if len(content.strip()) < 50:
                print(f"  ⏭️ Skipping {file_path.name} (too short)")
                continue
            
            print(f"\n📄 Processing: {source}/{file_path.name}")
            
            # Label with Gemini
            labels = label_prompt(content, source, file_path.name)
            
            if not labels:
                print(f"  ❌ Failed to label, skipping")
                failed += 1
                continue
            
            print(f"  📝 Category: {labels.get('category')}")
            print(f"  🔧 Techniques: {', '.join(labels.get('techniques', []))[:60]}...")
            
            if dry_run:
                print(f"  🔍 DRY RUN - would ingest")
                continue
            
            # Generate embedding
            embedding = get_embedding(content)
            
            # Create unique ID
            doc_id = f"sysprompt-{source.lower().replace(' ', '-')}-{file_path.stem.lower().replace(' ', '-')}"
            
            # Prepare metadata
            metadata = {
                "content": content[:8000],  # Pinecone metadata limit
                "source": source,
                "filename": file_path.name,
                "modality": "text",
                "dataset": "system-prompts",
                **labels
            }
            
            batch.append({
                "id": doc_id,
                "values": embedding,
                "metadata": metadata
            })
            
            processed += 1
            
            # Upsert in batches
            if len(batch) >= batch_size:
                print(f"\n📤 Upserting batch of {len(batch)} vectors...")
                index.upsert(vectors=batch, namespace="system-prompts")
                batch = []
                time.sleep(delay)
            
            # Rate limiting for Gemini
            time.sleep(0.5)
            
        except Exception as e:
            print(f"  ❌ Error processing {file_path}: {e}")
            failed += 1
    
    # Upsert remaining batch
    if batch and not dry_run:
        print(f"\n📤 Upserting final batch of {len(batch)} vectors...")
        index.upsert(vectors=batch, namespace="system-prompts")
    
    print(f"\n✅ Done! Processed: {processed}, Failed: {failed}")
    
    if not dry_run:
        # Get stats
        stats = index.describe_index_stats()
        print(f"📊 Total vectors in index: {stats.get('total_vector_count', 'unknown')}")


def main():
    parser = argparse.ArgumentParser(description="Label and ingest system prompts to Pinecone")
    parser.add_argument(
        "--repo-path",
        type=str,
        default="../system-prompts-and-models-of-ai-tools",
        help="Path to the system-prompts repository"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Batch size for Pinecone upserts"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay between batches (seconds)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Label prompts without ingesting to Pinecone"
    )
    
    args = parser.parse_args()
    
    repo_path = Path(args.repo_path).resolve()
    if not repo_path.exists():
        print(f"❌ Repository not found: {repo_path}")
        return
    
    print(f"🚀 System Prompts Labeling & Ingestion")
    print(f"📂 Repository: {repo_path}")
    print(f"🤖 Labeling model: {LABELING_MODEL}")
    print(f"📊 Target index: {PINECONE_INDEX_NAME}")
    print("")
    
    index = init_clients()
    process_and_ingest(
        repo_path,
        index,
        batch_size=args.batch_size,
        delay=args.delay,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()
