"""
Generate Specialized Marketing & Hyper-Realistic Video Prompts

Focus areas:
1. Marketing spokesperson videos with natural expressions
2. Product demonstrations with realistic human subjects
3. Skin realism - pores, texture, natural imperfections
4. Negative prompts for quality assurance
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

OUTPUT_FILE = Path(__file__).parent / "data" / "video_prompts_marketing.json"

GENERATION_PROMPT = """You are an expert video prompt engineer specializing in HYPER-REALISTIC MARKETING content. Generate 30 high-quality video prompts for modern AI video generation (Kling, Runway, Veo, Sora).

## CRITICAL FOCUS AREAS:

### 1. SKIN REALISM (Anti-AI-Smoothing)
- Explicit pore detail and skin texture
- Natural skin imperfections (freckles, subtle lines, varied skin tone)
- Realistic subsurface scattering (light through skin)
- Avoid: plastic skin, wax-like appearance, over-smoothed faces

### 2. MARKETING SPOKESPERSON VIDEOS
- Natural micro-expressions and subtle facial movements
- Authentic emotional delivery (not theatrical)
- Professional but approachable demeanor
- Clear lip sync and natural speech rhythm

### 3. PRODUCT DEMONSTRATIONS
- Hands with realistic knuckle texture and veins
- Natural finger movements (not robotic)
- Realistic product interaction (weight, texture feedback)

### 4. NEGATIVE PROMPTS (ESSENTIAL)
Include negative prompts to avoid:
- Over-smoothed skin, plastic appearance
- Uncanny valley expressions
- Unnatural eye movement
- Static hair, artificial lighting
- Robotic movements

## NEW CATEGORIES TO USE:
- "marketing_spokesperson" - Professional presenter speaking to camera
- "product_demo" - Hands-on product demonstration
- "testimonial" - Customer/user testimonial style
- "ugc_style" - User-generated content aesthetic (raw, authentic)
- "corporate_explainer" - Professional business content

## OUTPUT FORMAT (JSON Array):
[{
  "prompt": "Full detailed prompt with explicit realism instructions",
  "category": "marketing_spokesperson|product_demo|testimonial|ugc_style|corporate_explainer",
  "camera_movement": "Primary technique",
  "duration_suggestion": "5s-15s",
  "negative_prompt": "Specific things to AVOID for this prompt",
  "realism_notes": "Key realism elements emphasized"
}]

Generate 30 prompts covering all 5 categories evenly (6 per category).
Return ONLY the JSON array."""


def generate_marketing_prompts():
    """Generate specialized marketing and realistic prompts"""
    
    print("Configuring Gemini API...")
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash")
    
    print("Generating marketing & realism-focused prompts...")
    response = model.generate_content(
        GENERATION_PROMPT,
        generation_config={
            "temperature": 0.85,
            "max_output_tokens": 16384,
        }
    )
    
    response_text = response.text
    print(f"Received response ({len(response_text)} chars)")
    
    # Parse JSON
    try:
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]
        
        prompts = json.loads(response_text.strip())
        print(f"Successfully parsed {len(prompts)} prompts")
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print("Raw response:", response_text[:1000])
        return None
    
    # Save
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(prompts, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(prompts)} prompts to {OUTPUT_FILE}")
    
    # Show samples
    print("\n=== Sample Marketing Prompts ===")
    for i, p in enumerate(prompts[:3]):
        print(f"\n{i+1}. [{p.get('category', 'unknown')}]")
        print(f"   Prompt: {p['prompt'][:100]}...")
        print(f"   Negative: {p.get('negative_prompt', 'N/A')[:80]}...")
        print(f"   Realism: {p.get('realism_notes', 'N/A')}")
    
    return prompts


if __name__ == "__main__":
    generate_marketing_prompts()
