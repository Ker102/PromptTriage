"""
Generate Video Prompts using Gemini 3 Pro

Uses the existing GEMINI_API_KEY from .env.local - no additional setup needed!
"""

import json
import os
from pathlib import Path
import google.generativeai as genai

# Load API key from .env.local
ENV_FILE = Path(__file__).parent.parent.parent / "promptrefiner-ui" / ".env.local"
# Also try absolute path as fallback
ABSOLUTE_ENV_FILE = Path(r"c:\Users\krist\Desktop\Cursor-Projects\Projects\Systempromptfactory\PromptTriage\promptrefiner-ui\.env.local")
API_KEY = None

for env_path in [ENV_FILE, ABSOLUTE_ENV_FILE]:
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.startswith("GOOGLE_GEMINI_API_KEY="):
                    API_KEY = line.strip().split("=", 1)[1].strip('"').strip("'")
                    print(f"Found API key in {env_path}")
                    break
    if API_KEY:
        break

if not API_KEY:
    API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env.local or environment")

# Configuration
MODEL = "gemini-2.0-flash"  # Fast and capable
OUTPUT_FILE = Path(__file__).parent / "data" / "video_prompts_generated.json"

# Seed examples from our research
SEED_EXAMPLES = """
Here are example high-quality video generation prompts from leading platforms:

## Kling AI Examples:
1. "A mechanic in greasy overalls repairs a motorcycle engine in a small garage. The lighting is warm and cinematic, with deep shadows and vintage tones. Camera slowly pulls back as the mechanic works, revealing posters on the walls."
2. "Anthropomorphic fat red cat sitting on the chair at the outside table made of wood eating dumplings using his hands, bowl with dumplings on the table, 360 spin around the cat, photorealistic, cinematic."

## Google Veo Examples:
3. "A close-up of a weary woman in a red hoodie sipping coffee on a foggy balcony at dawn, steam rising from the cup, soft lo-fi music in the background."

## Higgsfield Examples:
4. "A slow cinematic orbit shot with a gradual dolly-in on a young woman standing in a dimly lit vintage kitchen. Her face is filled with rage and sorrow as she suddenly screams."
5. "The car screeches around a corner, tires skidding on wet asphalt. The camera jolts and shakes, mimicking the unpredictable lurches of the vehicle."

## Luma Dream Machine Examples:
6. "Dynamic wide angle tracking shot, camera follows a majestic eagle soaring high above snow-capped mountains, soft golden hour light, epic atmosphere."

## Runway Gen-3 Examples:
7. "Continuous hyperspace jump, star wars style, streaking lights and warped stars."
"""

GENERATION_PROMPT = """You are an expert video prompt engineer. Your task is to generate 50 high-quality video generation prompts based on the patterns and best practices shown in the examples.

{seed_examples}

## Best Practices to Follow:
1. **Structure**: [Subject] + [Action] + [Setting] + [Camera Movement] + [Lighting/Atmosphere]
2. **Camera Language**: Use cinematic terms (dolly-in, tracking shot, orbit, pan, tilt, crane, push in, pull out)
3. **Specificity**: Be detailed about textures, colors, lighting, mood
4. **Variety**: Cover different categories: cinematic, nature, sci-fi, fantasy, commercial, character animation, action

## Output Format:
Generate exactly 50 prompts as a JSON array. Each item should have:
- "prompt": The full video prompt text
- "category": One of [cinematic, nature, sci-fi, fantasy, commercial, character, action, abstract, documentary, music_video]
- "camera_movement": Primary camera technique used
- "duration_suggestion": Recommended clip length (e.g., "5s", "10s")

Return ONLY the JSON array, no other text or markdown."""


def generate_prompts():
    """Generate video prompts using Gemini"""
    
    print(f"Configuring Gemini API...")
    genai.configure(api_key=API_KEY)
    
    model = genai.GenerativeModel(MODEL)
    
    print(f"Generating prompts with {MODEL}...")
    response = model.generate_content(
        GENERATION_PROMPT.format(seed_examples=SEED_EXAMPLES),
        generation_config={
            "temperature": 0.9,
            "max_output_tokens": 8192,
        }
    )
    
    response_text = response.text
    print(f"Received response ({len(response_text)} chars)")
    
    # Parse JSON from response
    try:
        # Try to extract JSON if wrapped in markdown
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]
        
        prompts = json.loads(response_text.strip())
        print(f"Successfully parsed {len(prompts)} prompts")
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print("Raw response:", response_text[:500])
        return None
    
    # Save to file
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(prompts, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(prompts)} prompts to {OUTPUT_FILE}")
    return prompts


if __name__ == "__main__":
    prompts = generate_prompts()
    
    if prompts:
        print("\n=== Sample Generated Prompts ===")
        for i, p in enumerate(prompts[:5]):
            print(f"\n{i+1}. [{p.get('category', 'unknown')}] {p['prompt'][:100]}...")
