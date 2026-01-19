import os
import json
from firecrawl import FirecrawlApp

# Configuration
API_KEY = os.getenv('FIRECRAWL_API_KEY')
OUTPUT_FILE = 'backend/scripts/data/scraped_video_prompts.json'

URLS = [
    "https://help.runwayml.com/hc/en-us/articles/30586818553107-Gen-3-Alpha-Prompting-Guide",
    "https://lumalabs.ai/learning-hub/best-practices",
    "https://filmart.ai/luma-dream-machine/",
    "https://leonardo.ai/news/kling-ai-prompts/",
    "https://medium.com/@mattmajewski/exploring-pika-labs-the-ultimate-guide-to-creating-amazing-video-clips-cd947e6eee1f"
]

def scrape_prompts():
    if not API_KEY:
        print("Error: FIRECRAWL_API_KEY environment variable not set")
        return

    app = FirecrawlApp(api_key=API_KEY)
    all_prompts = []

    print(f"Starting scrape of {len(URLS)} URLs...")

    for url in URLS:
        try:
            print(f"Scraping {url}...")
            # We use the extract endpoint to get structured data directly if possible
            # But for now, let's just scrape the markdown and save it for processing
            # In a real scenario, we'd use LLM extraction on the markdown
            scrape_result = app.scrape_url(url, params={'formats': ['markdown']})
            
            if scrape_result and 'markdown' in scrape_result:
                print(f"Successfully scraped {url}")
                # Placeholder for where we would extract prompts from markdown
                # For this artifact, we're just saving the raw scrape reference
                all_prompts.append({
                    'source': url,
                    'content': scrape_result['markdown'][:500] + "..." # Truncated for preview
                })
        except Exception as e:
            print(f"Failed to scrape {url}: {e}")

    # Save results
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(all_prompts, f, indent=2)
    
    print(f"Scraping complete. Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    scrape_prompts()
