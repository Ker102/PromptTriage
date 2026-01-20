"""
Refine Generated Video Prompts - Quality Improvement Pass

Compare generated prompts to base examples and enhance weaker ones
to match the quality of professional platform prompts.
"""

import json
from pathlib import Path
import google.generativeai as genai

# Load API key
ENV_FILE = Path(r"c:\Users\krist\Desktop\Cursor-Projects\Projects\Systempromptfactory\PromptTriage\promptrefiner-ui\.env.local")
API_KEY = None
if ENV_FILE.exists():
    with open(ENV_FILE) as f:
        for line in f:
            if line.startswith("GOOGLE_GEMINI_API_KEY="):
                API_KEY = line.strip().split("=", 1)[1].strip('"').strip("'")
                break

if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found")

GENERATED_FILE = Path(__file__).parent / "data" / "video_prompts_generated.json"
OUTPUT_FILE = Path(__file__).parent / "data" / "video_prompts_refined.json"

# High-quality base examples for comparison
BASE_EXAMPLES = """
## Professional Quality Examples (from Kling, Higgsfield, Veo):

1. "A mechanic in greasy overalls repairs a motorcycle engine in a small garage. The lighting is warm and cinematic, with deep shadows and vintage tones. Camera slowly pulls back as the mechanic works, revealing posters on the walls."
   - ✓ Specific character details (greasy overalls)
   - ✓ Explicit lighting description (warm, deep shadows, vintage tones)
   - ✓ Camera movement IN the prompt text (slowly pulls back)
   - ✓ Scene reveal (posters on walls)

2. "A slow cinematic orbit shot with a gradual dolly-in on a young woman standing in a dimly lit vintage kitchen. Her face is filled with rage and sorrow as she suddenly screams."
   - ✓ Camera movement FIRST (slow orbit, dolly-in)
   - ✓ Emotional state (rage and sorrow)
   - ✓ Dynamic action (suddenly screams)
   - ✓ Atmospheric setting (dimly lit vintage kitchen)

3. "Anthropomorphic fat red cat sitting on the chair at the outside table made of wood eating dumplings using his hands, bowl with dumplings on the table, 360 spin around the cat, photorealistic, cinematic."
   - ✓ Highly specific character (fat red cat, anthropomorphic)
   - ✓ Precise props (wooden table, bowl, dumplings)
   - ✓ Camera movement (360 spin)
   - ✓ Style keywords (photorealistic, cinematic)
"""

REFINEMENT_PROMPT = """You are a video prompt engineering expert. Review and IMPROVE each prompt to match the quality standards of professional platforms like Kling, Higgsfield, and Veo.

{base_examples}

## Quality Criteria to Check:
1. **Camera Movement**: Must be EXPLICIT in the prompt text (not just metadata)
2. **Character Details**: Specific clothing, expressions, postures
3. **Lighting Description**: Explicit lighting terms (golden hour, neon glow, harsh shadows)
4. **Atmosphere/Mood**: Emotional descriptors (tense, serene, chaotic)
5. **Props/Environment Details**: Specific objects, textures, surroundings

## Prompts to Refine:
{prompts_to_refine}

## Instructions:
For each prompt, if it's already high quality, keep it unchanged.
If it needs improvement, enhance it following the criteria above.

Return the improved prompts as a JSON array with the same structure:
[{{"prompt": "...", "category": "...", "camera_movement": "...", "duration_suggestion": "..."}}]

ONLY return the JSON array, no other text."""


def refine_prompts():
    """Refine generated prompts to match base quality"""
    
    # Load generated prompts
    with open(GENERATED_FILE) as f:
        generated = json.load(f)
    
    print(f"Loaded {len(generated)} generated prompts")
    
    # Configure Gemini
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash")
    
    # Process in batches of 10
    batch_size = 15
    refined_all = []
    
    for i in range(0, len(generated), batch_size):
        batch = generated[i:i+batch_size]
        print(f"Refining batch {i//batch_size + 1} ({len(batch)} prompts)...")
        
        batch_json = json.dumps(batch, indent=2)
        
        response = model.generate_content(
            REFINEMENT_PROMPT.format(
                base_examples=BASE_EXAMPLES,
                prompts_to_refine=batch_json
            ),
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 8192,
            }
        )
        
        response_text = response.text
        
        # Parse JSON
        try:
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            refined_batch = json.loads(response_text.strip())
            refined_all.extend(refined_batch)
            print(f"  Refined {len(refined_batch)} prompts in this batch")
        except json.JSONDecodeError as e:
            print(f"  JSON parse error in batch: {e}")
            # Keep original if parsing fails
            refined_all.extend(batch)
    
    # Save refined prompts
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(refined_all, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved {len(refined_all)} refined prompts to {OUTPUT_FILE}")
    
    # Show comparison
    print("\n=== Before/After Comparison (first 3) ===")
    for i in range(min(3, len(generated))):
        print(f"\n--- Prompt {i+1} ---")
        print(f"BEFORE: {generated[i]['prompt'][:120]}...")
        print(f"AFTER:  {refined_all[i]['prompt'][:120]}...")
    
    return refined_all


if __name__ == "__main__":
    refine_prompts()
