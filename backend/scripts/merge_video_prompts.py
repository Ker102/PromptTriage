"""
Merge All Video Prompt Datasets

Combines:
1. Base prompts (6) - Original scraped examples
2. Refined prompts (51) - AI-generated + quality refined  
3. Marketing prompts (30) - Specialized realistic marketing with negative prompts

Creates a unified dataset for Pinecone ingestion.
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_FILE = DATA_DIR / "video_prompts_complete.json"

def merge_datasets():
    """Merge all video prompt datasets into one comprehensive file"""
    
    all_prompts = []
    
    # 1. Base prompts (original scraped)
    base_file = DATA_DIR / "video_prompts.json"
    if base_file.exists():
        with open(base_file) as f:
            base = json.load(f)
            # Normalize structure
            for p in base:
                normalized = {
                    "prompt": p["prompt"],
                    "category": p.get("category", "cinematic"),
                    "platform": p.get("platform", "mixed"),
                    "camera_movement": p.get("elements", {}).get("camera", "not specified"),
                    "duration_suggestion": "8s",
                    "negative_prompt": None,
                    "realism_notes": None,
                    "source": "scraped_base"
                }
                all_prompts.append(normalized)
        print(f"✓ Loaded {len(base)} base prompts")
    
    # 2. Refined prompts (AI-generated and quality refined)
    refined_file = DATA_DIR / "video_prompts_refined.json"
    if refined_file.exists():
        with open(refined_file) as f:
            refined = json.load(f)
            for p in refined:
                normalized = {
                    "prompt": p["prompt"],
                    "category": p.get("category", "cinematic"),
                    "platform": "ai_generated",
                    "camera_movement": p.get("camera_movement", "not specified"),
                    "duration_suggestion": p.get("duration_suggestion", "8s"),
                    "negative_prompt": None,
                    "realism_notes": None,
                    "source": "gemini_refined"
                }
                all_prompts.append(normalized)
        print(f"✓ Loaded {len(refined)} refined prompts")
    
    # 3. Marketing prompts (specialized with negative prompts)
    marketing_file = DATA_DIR / "video_prompts_marketing.json"
    if marketing_file.exists():
        with open(marketing_file) as f:
            marketing = json.load(f)
            for p in marketing:
                normalized = {
                    "prompt": p["prompt"],
                    "category": p.get("category", "marketing_spokesperson"),
                    "platform": "ai_generated",
                    "camera_movement": p.get("camera_movement", "not specified"),
                    "duration_suggestion": p.get("duration_suggestion", "8s"),
                    "negative_prompt": p.get("negative_prompt"),
                    "realism_notes": p.get("realism_notes"),
                    "source": "gemini_marketing"
                }
                all_prompts.append(normalized)
        print(f"✓ Loaded {len(marketing)} marketing prompts")
    
    # Save merged dataset
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_prompts, f, indent=2, ensure_ascii=False)
    
    # Summary statistics
    categories = {}
    for p in all_prompts:
        cat = p["category"]
        categories[cat] = categories.get(cat, 0) + 1
    
    print(f"\n=== MERGED DATASET SUMMARY ===")
    print(f"Total prompts: {len(all_prompts)}")
    print(f"With negative prompts: {sum(1 for p in all_prompts if p['negative_prompt'])}")
    print(f"With realism notes: {sum(1 for p in all_prompts if p['realism_notes'])}")
    print(f"\nCategories:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")
    
    print(f"\nSaved to: {OUTPUT_FILE}")
    return all_prompts


if __name__ == "__main__":
    merge_datasets()
