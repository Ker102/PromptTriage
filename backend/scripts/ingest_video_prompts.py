#!/usr/bin/env python3
"""
Video Prompts Ingestion Script

Ingests video prompts and negative prompts into Pinecone namespaces:
- video-prompts: 86 complete video prompts
- video-negative-prompts: 12 categories of curated negative prompts

Usage:
    py scripts/ingest_video_prompts.py
    py scripts/ingest_video_prompts.py --namespace video-prompts
    py scripts/ingest_video_prompts.py --namespace video-negative-prompts
    py scripts/ingest_video_prompts.py --namespace all
"""

import argparse
import json
import time
import uuid
import sys
from pathlib import Path

import google.generativeai as genai
from pinecone import Pinecone
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

DATA_DIR = Path(__file__).parent / "data"


def embed_text(text: str) -> list[float]:
    """Generate embedding using Gemini embedding-001."""
    result = genai.embed_content(
        model="models/embedding-001",
        content=text,
        task_type="retrieval_document",
    )
    return result["embedding"]


def ingest_video_prompts(index, delay_ms: int = 50):
    """Ingest video prompts into video-prompts namespace."""
    
    input_file = DATA_DIR / "video_prompts_complete.json"
    namespace = "video-prompts"
    
    print(f"\n{'='*60}")
    print(f"INGESTING VIDEO PROMPTS")
    print(f"Source: {input_file}")
    print(f"Namespace: {namespace}")
    print(f"{'='*60}\n")
    
    if not input_file.exists():
        print(f"ERROR: {input_file} not found!")
        return 0
    
    with open(input_file, "r", encoding="utf-8") as f:
        prompts = json.load(f)
    
    print(f"Loaded {len(prompts)} video prompts")
    
    vectors = []
    total_ingested = 0
    total_errors = 0
    batch_size = 25
    
    for i, prompt_data in enumerate(prompts):
        try:
            # Create searchable content combining prompt + metadata
            prompt_text = prompt_data["prompt"]
            category = prompt_data.get("category", "cinematic")
            
            # Content for embedding includes category for better search
            embed_content = f"[{category}] {prompt_text}"
            
            embedding = embed_text(embed_content)
            
            doc_id = f"video-{uuid.uuid4()}"
            metadata = {
                "content": prompt_text[:2000],  # Pinecone metadata limit
                "category": category,
                "platform": prompt_data.get("platform", "ai_generated"),
                "camera_movement": prompt_data.get("camera_movement", ""),
                "duration_suggestion": prompt_data.get("duration_suggestion", ""),
                "negative_prompt": (prompt_data.get("negative_prompt") or "")[:500],
                "realism_notes": (prompt_data.get("realism_notes") or "")[:500],
                "source": prompt_data.get("source", "unknown"),
                "type": "video_prompt"
            }
            
            vectors.append((doc_id, embedding, metadata))
            
            if delay_ms > 0:
                time.sleep(delay_ms / 1000)
            
            if len(vectors) >= batch_size:
                index.upsert(vectors=vectors, namespace=namespace)
                total_ingested += len(vectors)
                print(f"  ✓ Ingested {total_ingested}/{len(prompts)} ({100*total_ingested//len(prompts)}%)")
                vectors = []
                
        except Exception as e:
            total_errors += 1
            print(f"  ✗ Error on prompt {i}: {e}")
            if total_errors > 10:
                print("  Too many errors, aborting")
                break
    
    # Upsert remaining
    if vectors:
        index.upsert(vectors=vectors, namespace=namespace)
        total_ingested += len(vectors)
    
    print(f"\n✓ Video prompts: {total_ingested} ingested, {total_errors} errors")
    return total_ingested


def ingest_negative_prompts(index, delay_ms: int = 50):
    """Ingest negative prompts library into video-negative-prompts namespace."""
    
    input_file = DATA_DIR / "video_negative_prompts_library.json"
    namespace = "video-negative-prompts"
    
    print(f"\n{'='*60}")
    print(f"INGESTING NEGATIVE PROMPTS LIBRARY")
    print(f"Source: {input_file}")
    print(f"Namespace: {namespace}")
    print(f"{'='*60}\n")
    
    if not input_file.exists():
        print(f"ERROR: {input_file} not found!")
        return 0
    
    with open(input_file, "r", encoding="utf-8") as f:
        categories = json.load(f)
    
    print(f"Loaded {len(categories)} negative prompt categories")
    
    vectors = []
    total_ingested = 0
    total_errors = 0
    
    for cat_data in categories:
        try:
            category = cat_data["category"]
            description = cat_data.get("description", "")
            negative_prompts = cat_data.get("negative_prompts", [])
            positive_alternatives = cat_data.get("positive_alternatives", [])
            platforms = cat_data.get("platform_compatibility", [])
            notes = cat_data.get("notes", "")
            
            # Create searchable content
            negatives_text = ", ".join(negative_prompts)
            positives_text = ", ".join(positive_alternatives)
            embed_content = f"[{category}] {description}. Avoid: {negatives_text}. Use instead: {positives_text}"
            
            embedding = embed_text(embed_content)
            
            doc_id = f"neg-{category}-{uuid.uuid4()}"
            metadata = {
                "category": category,
                "description": description[:500],
                "negative_prompts": negatives_text[:1500],
                "positive_alternatives": positives_text[:500],
                "platform_compatibility": ",".join(platforms),
                "notes": notes[:500],
                "type": "negative_prompt_category"
            }
            
            vectors.append((doc_id, embedding, metadata))
            
            if delay_ms > 0:
                time.sleep(delay_ms / 1000)
            
            print(f"  ✓ Embedded category: {category} ({len(negative_prompts)} negatives)")
                
        except Exception as e:
            total_errors += 1
            print(f"  ✗ Error on category {category}: {e}")
    
    # Upsert all at once (small dataset)
    if vectors:
        index.upsert(vectors=vectors, namespace=namespace)
        total_ingested = len(vectors)
    
    print(f"\n✓ Negative prompt categories: {total_ingested} ingested, {total_errors} errors")
    return total_ingested


def main():
    parser = argparse.ArgumentParser(description="Ingest video prompts into Pinecone")
    parser.add_argument(
        "--namespace", 
        type=str, 
        default="all",
        choices=["video-prompts", "video-negative-prompts", "all"],
        help="Which namespace to ingest"
    )
    parser.add_argument("--delay", type=int, default=50, help="Delay between embeddings (ms)")
    args = parser.parse_args()
    
    # Check environment variables
    google_api_key = os.getenv("GOOGLE_API_KEY")
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    pinecone_index_name = os.getenv("PINECONE_INDEX_NAME", "prompttriage-prompts")
    
    if not google_api_key or not pinecone_api_key:
        print("ERROR: GOOGLE_API_KEY and PINECONE_API_KEY must be set in .env")
        sys.exit(1)
    
    # Configure APIs
    genai.configure(api_key=google_api_key)
    pc = Pinecone(api_key=pinecone_api_key)
    index = pc.Index(pinecone_index_name)
    
    print(f"\n{'#'*60}")
    print(f"VIDEO PROMPTS PINECONE INGESTION")
    print(f"Index: {pinecone_index_name}")
    print(f"Target namespace(s): {args.namespace}")
    print(f"{'#'*60}")
    
    total_video = 0
    total_negative = 0
    
    if args.namespace in ["video-prompts", "all"]:
        total_video = ingest_video_prompts(index, args.delay)
    
    if args.namespace in ["video-negative-prompts", "all"]:
        total_negative = ingest_negative_prompts(index, args.delay)
    
    # Print final stats
    print(f"\n{'='*60}")
    print(f"INGESTION COMPLETE")
    print(f"{'='*60}")
    
    stats = index.describe_index_stats()
    print(f"\nPinecone Index Stats:")
    print(f"  Total vectors: {stats.total_vector_count}")
    print(f"\n  Namespaces:")
    for ns, ns_stats in stats.namespaces.items():
        print(f"    - {ns}: {ns_stats.vector_count} vectors")


if __name__ == "__main__":
    main()
