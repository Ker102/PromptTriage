#!/usr/bin/env python3
"""
Dataset Ingestion Script for PromptTriage RAG

Reads Parquet files from the datasets directory and ingests them
directly to Pinecone using Gemini embeddings.

Usage:
    cd backend
    py scripts/ingest_datasets.py [--batch-size N] [--delay MS] [--dataset NAME]
"""

import argparse
import time
import uuid
import sys
from pathlib import Path

import pandas as pd
import google.generativeai as genai
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Dataset configurations
DATASETS = {
    "ads_corporate": {
        "path": "datasets/ads_corporate",
        "prompt_column": "prompts",
        "category": "ads_corporate",
        "description": "Corporate and advertising prompts",
    },
    "photorealistic": {
        "path": "datasets/photorealistic", 
        "prompt_column": "prompts",
        "category": "photorealistic",
        "description": "Photorealistic image generation prompts",
    },
    "categorized": {
        "path": "datasets/categorized",
        "prompt_column": "prompt",
        "category": "categorized",
        "description": "Categorized prompts with subcategories and tags",
        "extra_columns": ["category", "subcategory", "tags"],
    },
}

# Category label mappings for categorized dataset
CATEGORY_LABELS = {
    0: "people", 1: "animals", 2: "food", 3: "objects",
    4: "vehicles", 5: "architecture", 6: "places",
}

SUBCATEGORY_LABELS = {
    0: "portrait", 1: "home-cooked meal", 2: "beach", 3: "action shot",
    4: "countryside", 5: "futuristic building", 6: "household pet",
    7: "common household object", 8: "exotic animal", 9: "modeling photoshoot",
    10: "forest", 11: "cityscape", 12: "ancient building", 13: "headshot",
    14: "spacecraft", 15: "wrapped food product", 16: "close-up",
    17: "fresh produce", 18: "industrial building", 19: "alien object",
    20: "marine vehicle", 21: "common outdoor animal", 22: "body part macro",
    23: "restaurant meal", 24: "alien animal", 25: "aircraft",
    26: "exotic object", 27: "profile", 28: "product packaging",
    29: "modern building", 30: "slice of life", 31: "land vehicle",
}


def find_parquet_file(directory: Path) -> Path:
    """Find the first parquet file in a directory."""
    parquet_files = list(directory.glob("*.parquet"))
    if not parquet_files:
        raise FileNotFoundError(f"No parquet files found in {directory}")
    return parquet_files[0]


def load_dataset(config: dict, base_path: Path) -> list[dict]:
    """Load a dataset and convert to documents for ingestion."""
    dataset_path = base_path / config["path"]
    parquet_file = find_parquet_file(dataset_path)
    
    print(f"  Loading {parquet_file.name}...")
    df = pd.read_parquet(parquet_file)
    
    documents = []
    prompt_col = config["prompt_column"]
    
    for _, row in df.iterrows():
        prompt = str(row[prompt_col]).strip()
        if not prompt:
            continue
        
        metadata = {
            "source": config["category"],
            "dataset": config["description"],
        }
        
        # Handle categorized dataset with extra columns
        if "extra_columns" in config:
            if "category" in row and pd.notna(row["category"]):
                cat_idx = int(row["category"])
                metadata["image_category"] = CATEGORY_LABELS.get(cat_idx, str(cat_idx))
            
            if "subcategory" in row and pd.notna(row["subcategory"]):
                subcat_idx = int(row["subcategory"])
                metadata["subcategory"] = SUBCATEGORY_LABELS.get(subcat_idx, str(subcat_idx))
            
            if "tags" in row and pd.notna(row["tags"]):
                metadata["tags"] = str(row["tags"])
        
        documents.append({
            "content": prompt,
            "metadata": metadata,
        })
    
    return documents


def embed_text(text: str) -> list[float]:
    """Generate embedding using Gemini embedding-001."""
    result = genai.embed_content(
        model="models/embedding-001",
        content=text,
        task_type="retrieval_document",
    )
    return result["embedding"]


def main():
    parser = argparse.ArgumentParser(description="Ingest datasets into Pinecone with Gemini embeddings")
    parser.add_argument("--batch-size", type=int, default=50, help="Vectors per Pinecone upsert")
    parser.add_argument("--delay", type=int, default=100, help="Delay between embeddings (ms)")
    parser.add_argument("--dataset", choices=list(DATASETS.keys()), help="Specific dataset to ingest")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of prompts (0 = all)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be ingested without sending")
    args = parser.parse_args()
    
    # Check environment variables
    google_api_key = os.getenv("GOOGLE_API_KEY")
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    pinecone_index_name = os.getenv("PINECONE_INDEX_NAME", "prompttriage-prompts")
    pinecone_env = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
    
    if not google_api_key:
        print("ERROR: GOOGLE_API_KEY not set in .env")
        sys.exit(1)
    
    if not pinecone_api_key:
        print("ERROR: PINECONE_API_KEY not set in .env")
        sys.exit(1)
    
    # Configure APIs
    genai.configure(api_key=google_api_key)
    pc = Pinecone(api_key=pinecone_api_key)
    
    # Create index if needed
    if pinecone_index_name not in pc.list_indexes().names():
        print(f"Creating Pinecone index '{pinecone_index_name}'...")
        pc.create_index(
            name=pinecone_index_name,
            dimension=768,  # Gemini embedding-001 dimension
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region=pinecone_env),
        )
        time.sleep(5)  # Wait for index to be ready
    
    index = pc.Index(pinecone_index_name)
    
    # Find project root
    script_dir = Path(__file__).parent
    base_path = script_dir.parent.parent  # backend/scripts -> backend -> PromptTriage
    
    print(f"Project root: {base_path}")
    print(f"Pinecone index: {pinecone_index_name}")
    print(f"Batch size: {args.batch_size}")
    print(f"Delay between embeddings: {args.delay}ms")
    print()
    
    # Select datasets to process
    datasets_to_process = [args.dataset] if args.dataset else list(DATASETS.keys())
    
    total_ingested = 0
    total_errors = 0
    
    for dataset_name in datasets_to_process:
        config = DATASETS[dataset_name]
        print(f"Processing: {dataset_name}")
        
        try:
            documents = load_dataset(config, base_path)
            
            if args.limit > 0:
                documents = documents[:args.limit]
            
            print(f"  Loaded {len(documents)} prompts")
            
            if args.dry_run:
                print(f"  [DRY RUN] Would ingest {len(documents)} documents")
                print(f"  Sample: {documents[0]['content'][:100]}...")
                continue
            
            # Ingest with rate limiting
            vectors = []
            
            for i, doc in enumerate(documents):
                try:
                    # Generate embedding
                    embedding = embed_text(doc["content"])
                    
                    # Prepare vector
                    doc_id = str(uuid.uuid4())
                    metadata = doc["metadata"].copy()
                    metadata["content"] = doc["content"][:1000]  # Truncate for metadata limit
                    
                    vectors.append((doc_id, embedding, metadata))
                    
                    # Rate limiting
                    if args.delay > 0:
                        time.sleep(args.delay / 1000)
                    
                    # Batch upsert
                    if len(vectors) >= args.batch_size:
                        index.upsert(vectors=vectors)
                        total_ingested += len(vectors)
                        print(f"  Ingested {total_ingested}/{len(documents)} ({100*total_ingested//len(documents)}%)")
                        vectors = []
                    
                except Exception as e:
                    total_errors += 1
                    print(f"  Error on doc {i}: {e}")
                    if total_errors > 10:
                        print("  Too many errors, aborting dataset")
                        break
                    continue
            
            # Upsert remaining
            if vectors:
                index.upsert(vectors=vectors)
                total_ingested += len(vectors)
            
            print(f"  ✓ Completed {dataset_name}: {total_ingested} ingested, {total_errors} errors")
            
        except FileNotFoundError as e:
            print(f"  ✗ Error: {e}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
        
        print()
    
    print(f"\n{'='*50}")
    print(f"TOTAL INGESTED: {total_ingested} documents")
    print(f"TOTAL ERRORS: {total_errors}")
    
    # Show index stats
    stats = index.describe_index_stats()
    print(f"Pinecone index now has: {stats.total_vector_count} vectors")


if __name__ == "__main__":
    main()
