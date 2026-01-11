#!/usr/bin/env python3
"""
JSON Prompts Ingestion Script

Ingests prompts from a JSON file (extracted by extract_hf_prompts.py)
into Pinecone using Gemini embeddings.

Usage:
    py scripts/ingest_json_prompts.py --input datasets/open-image-preferences_prompts.json
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


def embed_text(text: str) -> list[float]:
    """Generate embedding using Gemini embedding-001."""
    result = genai.embed_content(
        model="models/embedding-001",
        content=text,
        task_type="retrieval_document",
    )
    return result["embedding"]


def main():
    parser = argparse.ArgumentParser(description="Ingest JSON prompts into Pinecone")
    parser.add_argument("--input", type=Path, required=True, help="Input JSON file")
    parser.add_argument("--batch-size", type=int, default=50, help="Vectors per upsert")
    parser.add_argument("--delay", type=int, default=50, help="Delay between embeddings (ms)")
    parser.add_argument("--limit", type=int, default=0, help="Limit prompts (0 = all)")
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
    
    # Load prompts
    print(f"Loading prompts from {args.input}")
    with open(args.input, "r", encoding="utf-8") as f:
        prompts = json.load(f)
    
    if args.limit > 0:
        prompts = prompts[:args.limit]
    
    print(f"Loaded {len(prompts)} prompts")
    print(f"Pinecone index: {pinecone_index_name}")
    print()
    
    # Ingest
    vectors = []
    total_ingested = 0
    total_errors = 0
    
    for i, prompt in enumerate(prompts):
        try:
            embedding = embed_text(prompt["content"])
            
            doc_id = str(uuid.uuid4())
            metadata = prompt.get("metadata", {})
            metadata["content"] = prompt["content"][:1000]
            
            vectors.append((doc_id, embedding, metadata))
            
            if args.delay > 0:
                time.sleep(args.delay / 1000)
            
            if len(vectors) >= args.batch_size:
                index.upsert(vectors=vectors)
                total_ingested += len(vectors)
                print(f"  Ingested {total_ingested}/{len(prompts)} ({100*total_ingested//len(prompts)}%)")
                vectors = []
                
        except Exception as e:
            total_errors += 1
            print(f"  Error on prompt {i}: {e}")
            if total_errors > 10:
                print("  Too many errors, aborting")
                break
    
    # Upsert remaining
    if vectors:
        index.upsert(vectors=vectors)
        total_ingested += len(vectors)
    
    print(f"\n{'='*50}")
    print(f"TOTAL INGESTED: {total_ingested}")
    print(f"TOTAL ERRORS: {total_errors}")
    
    stats = index.describe_index_stats()
    print(f"Pinecone index now has: {stats.total_vector_count} vectors")


if __name__ == "__main__":
    main()
