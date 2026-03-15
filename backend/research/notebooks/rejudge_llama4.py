import os
import sys
import json
import time
import subprocess
import requests
from pathlib import Path

# Add parent directory to path to import original script functions
current_dir = Path(r"c:\Users\krist\Desktop\Cursor-Projects\Projects\Systempromptfactory\PromptTriage\backend\research\notebooks")
sys.path.append(str(current_dir))

from study_d_behavioral import BEHAVIORAL_JUDGE_USER, BEHAVIORAL_JUDGE_SYSTEM, OUTPUT_DIR

class Llama4JudgeProvider:
    """Llama 4 Maverick (17B-128E MoE) via Vertex AI MaaS HTTP."""
    NAME = "llama_4_maverick"

    def __init__(self):
        self.project_id = os.getenv("VERTEX_PROJECT_ID", "modelsandtraining")
        self.region = "us-east5"
        self.model_name = "meta/llama-4-maverick-17b-128e-instruct-maas"
        
        # Get gcloud token
        result = subprocess.run(
            "gcloud auth print-access-token", 
            shell=True, capture_output=True, text=True, check=True
        )
        self.token = result.stdout.strip()
        
        self.url = f"https://{self.region}-aiplatform.googleapis.com/v1beta1/projects/{self.project_id}/locations/{self.region}/endpoints/openapi/chat/completions"

    def generate_json(self, user_msg: str, system_prompt: str = None) -> str:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_msg})
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 1024,
            "stream": False,
            "response_format": {"type": "json_object"}
        }
        
        for attempt in range(3):
            try:
                resp = requests.post(self.url, headers=headers, json=payload, timeout=20)
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"]
                elif resp.status_code == 401:
                    # Refresh token
                    print("  [Judge] Token expired. Refreshing...")
                    result = subprocess.run(
                        "gcloud auth print-access-token", 
                        shell=True, capture_output=True, text=True, check=True
                    )
                    self.token = result.stdout.strip()
                    headers["Authorization"] = f"Bearer {self.token}"
                else:
                    print(f"    [Judge API Error on attempt {attempt+1}]: {resp.status_code} - {resp.text[:100]}")
            except Exception as e:
                print(f"    [Judge Request Error on attempt {attempt+1}]: {e}")
            
            time.sleep(2 ** attempt)
            if attempt == 2:
                raise Exception("Llama 4 API failed after 3 attempts")


def rejudge_all():
    judge = Llama4JudgeProvider()
    
    backup_dir = OUTPUT_DIR / "gemini_judged_backup"
    
    for backup_file in sorted(backup_dir.glob("study_d_behavioral_*.json")):
        print(f"\n==================================================")
        print(f"Re-judging {backup_file.name} with Llama 4 Maverick...")
        print(f"==================================================")
        
        data = json.loads(backup_file.read_text(encoding="utf-8"))
        
        target_file = OUTPUT_DIR / backup_file.name
        new_results = []
        
        for idx, item in enumerate(data, 1):
            task_id = item["task_id"]
            category = item["category"]
            model_output = item["output"]
            
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
                
                dims = ["role_expertise", "edge_cases", "specificity", "boundaries", "format"]
                for d in dims:
                    scores[d] = max(1, min(10, int(scores.get(d, 5))))
                scores["total"] = sum(scores[d] for d in dims)
                
                print(f" {scores['total']}/50")
                item["judge_model"] = judge.NAME # Track who judged it
                
            except Exception as e:
                print(f" ERROR: JSON Parse/API failure: {e}")
                scores = {
                    "role_expertise": 0, "edge_cases": 0, "specificity": 0, "boundaries": 0, "format": 0,
                    "total": 0, "reasoning": f"Llama judge error: {e}"
                }
            
            item["scores"] = scores
            new_results.append(item)
            
            target_file.write_text(json.dumps(new_results, indent=2, ensure_ascii=False), encoding="utf-8")
        
    print("\n✅ All re-judging complete. Run `python study_d_behavioral.py --summary` to see new totals.")

if __name__ == "__main__":
    rejudge_all()
