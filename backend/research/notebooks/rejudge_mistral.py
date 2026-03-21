import os
import sys
import json
import time
from pathlib import Path
from google import genai
from google.genai import types

# Add parent directory to path to import original script functions
current_dir = Path(r"c:\Users\krist\Desktop\Cursor-Projects\Projects\Systempromptfactory\PromptTriage\backend\research\notebooks")
sys.path.append(str(current_dir))

from study_d_behavioral import BEHAVIORAL_JUDGE_USER, BEHAVIORAL_JUDGE_SYSTEM, OUTPUT_DIR

class MistralJudgeProvider:
    """Mistral Large 3 via Vertex AI."""
    NAME = "mistral_large_3"

    def __init__(self):
        project_id = os.getenv("VERTEX_PROJECT_ID", "modelsandtraining")
        location = "europe-west1" # Mistral is typically in eu-west1 or us-central1
        
        # New Google GenAI SDK (recommended for Vertex AI going forward)
        self.client = genai.Client(vertexai=True, project=project_id, location=location)
        self.model = "mistral-large-3" # The ID the user provided

    def generate_json(self, user_msg: str, system_prompt: str = None) -> str:
        # Mistral handles JSON mode well via standard prompting or schema
        # We will use the system instruction and low temperature
        config = types.GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=2048,
            system_instruction=system_prompt,
            response_mime_type="application/json"
        )
        
        # Retry logic for quota/rate limits
        for attempt in range(3):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=user_msg,
                    config=config
                )
                return response.text
            except Exception as e:
                print(f"    [Judge Error on attempt {attempt+1}]: {e}")
                time.sleep(2 ** attempt)
                if attempt == 2:
                    raise e


def rejudge_all():
    judge = MistralJudgeProvider()
    
    # Process all 8 files
    backup_dir = OUTPUT_DIR / "gemini_judged_backup"
    
    for backup_file in sorted(backup_dir.glob("study_d_behavioral_*.json")):
        print(f"\n==================================================")
        print(f"Re-judging {backup_file.name} with Mistral...")
        print(f"==================================================")
        
        data = json.loads(backup_file.read_text(encoding="utf-8"))
        
        # We'll save to the main OUTPUT_DIR to overwrite the old Gemini ones
        target_file = OUTPUT_DIR / backup_file.name
        new_results = []
        
        for idx, item in enumerate(data, 1):
            task_id = item["task_id"]
            category = item["category"]
            model_output = item["output"]
            
            # Reconstruct the user evaluation prompt
            # To get the original 'task', we extract it if we didn't save it directly.
            # Wait, the original script didn't save the raw prompt in the JSON.
            # I need to fetch it from BEHAVIORAL_TASKS
            from study_d_behavioral import BEHAVIORAL_TASKS
            task_obj = next((t for t in BEHAVIORAL_TASKS if t["id"] == task_id), None)
            if not task_obj:
                print(f"  [{idx}/{len(data)}] Skipping {task_id} (not found)")
                continue
                
            task_text = task_obj["task"]
            user_msg = BEHAVIORAL_JUDGE_USER.format(category=category, task=task_text, response=model_output)
            
            print(f"  [{idx}/{len(data)}] Judging {task_id}...", end="", flush=True)
            
            try:
                raw_json = judge.generate_json(user_msg, system_prompt=BEHAVIORAL_JUDGE_SYSTEM)
                scores = json.loads(raw_json.strip())
                
                # Enforce bounds
                dims = ["role_expertise", "edge_cases", "specificity", "boundaries", "format"]
                for d in dims:
                    scores[d] = max(1, min(10, int(scores.get(d, 5))))
                scores["total"] = sum(scores[d] for d in dims)
                
                print(f" {scores['total']}/50")
                
            except Exception as e:
                print(f" ERROR: JSON Parse/API failure: {e}")
                scores = {
                    "role_expertise": 0, "edge_cases": 0, "specificity": 0, "boundaries": 0, "format": 0,
                    "total": 0, "reasoning": f"Mistral judge error: {e}"
                }
            
            # Update the item with new scores
            item["scores"] = scores
            new_results.append(item)
            
            # Save progressively
            target_file.write_text(json.dumps(new_results, indent=2, ensure_ascii=False), encoding="utf-8")
        
    print("\n✅ All re-judging complete. Run `python study_d_behavioral.py --summary` to see new totals.")

if __name__ == "__main__":
    rejudge_all()
