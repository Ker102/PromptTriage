#!/usr/bin/env python3
"""
Dataset Ingestion Script for PromptTriage RAG

Reads Parquet files from the datasets directory and ingests them
into Redis Vector Store via the RAG API.

Usage:
    python scripts/ingest_datasets.py [--api-url URL] [--batch-size N]
"""

import argparse
import json
import sys
from pathlib import Path

import httpx
import pandas as pd

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


def ingest_batch(client: httpx.Client, api_url: str, documents: list[dict]) -> int:
    """Send a batch of documents to the ingestion API."""
    response = client.post(
        f"{api_url}/api/rag/ingest/batch",
        json={"documents": documents},
        timeout=60.0,
    )
    response.raise_for_status()
    result = response.json()
    return result.get("count", 0)


def main():
    parser = argparse.ArgumentParser(description="Ingest datasets into Redis Vector Store")
    parser.add_argument("--api-url", default="http://localhost:8000", help="Backend API URL")
    parser.add_argument("--batch-size", type=int, default=100, help="Documents per batch")
    parser.add_argument("--dataset", choices=list(DATASETS.keys()), help="Specific dataset to ingest")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be ingested without sending")
    args = parser.parse_args()
    
    # Find project root (parent of backend/)
    script_dir = Path(__file__).parent
    base_path = script_dir.parent.parent  # backend/scripts -> backend -> PromptTriage
    
    print(f"Project root: {base_path}")
    print(f"API URL: {args.api_url}")
    print(f"Batch size: {args.batch_size}")
    print()
    
    # Select datasets to process
    datasets_to_process = [args.dataset] if args.dataset else list(DATASETS.keys())
    
    total_ingested = 0
    
    with httpx.Client() as client:
        for dataset_name in datasets_to_process:
            config = DATASETS[dataset_name]
            print(f"Processing: {dataset_name}")
            
            try:
                documents = load_dataset(config, base_path)
                print(f"  Loaded {len(documents)} prompts")
                
                if args.dry_run:
                    print(f"  [DRY RUN] Would ingest {len(documents)} documents")
                    print(f"  Sample: {documents[0]['content'][:100]}...")
                    continue
                
                # Ingest in batches
                for i in range(0, len(documents), args.batch_size):
                    batch = documents[i:i + args.batch_size]
                    ingested = ingest_batch(client, args.api_url, batch)
                    total_ingested += ingested
                    print(f"  Ingested batch {i // args.batch_size + 1}: {ingested} documents")
                
                print(f"  ✓ Completed {dataset_name}")
                
            except FileNotFoundError as e:
                print(f"  ✗ Error: {e}")
            except httpx.HTTPError as e:
                print(f"  ✗ API Error: {e}")
            except Exception as e:
                print(f"  ✗ Error: {e}")
            
            print()
    
    print(f"Total ingested: {total_ingested} documents")


if __name__ == "__main__":
    main()
