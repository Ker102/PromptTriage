#!/usr/bin/env python3
"""
Prompt Pattern Analysis Script

Analyzes all system prompts from system-prompts-reference/ to extract:
- Common XML/structural tags per vendor
- Section frequencies
- Word count and style statistics
- Vendor-specific patterns

Outputs: prompt_patterns.json
"""

import os
import sys
import json
import re
from pathlib import Path
from collections import Counter, defaultdict

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')


def find_prompt_files(repo_path: Path) -> list[tuple[Path, str]]:
    """Find all prompt files."""
    prompt_files = []
    
    for ext in ["*.txt", "*.md", "*.xml", "*.js"]:
        for fp in repo_path.rglob(ext):
            if fp.name.lower() in ["license.md", "readme.md", ".gitignore"]:
                continue
            if any(p.startswith(".") for p in fp.parts):
                continue
            if "old" in [p.lower() for p in fp.parts]:
                continue
            rel = fp.relative_to(repo_path)
            vendor = rel.parts[0].lower() if len(rel.parts) > 1 else "misc"
            prompt_files.append((fp, vendor))
    
    # Extensionless files
    for fp in repo_path.rglob("*"):
        if fp.is_file() and not fp.suffix:
            if fp.name.startswith("."):
                continue
            if any(p.startswith(".") for p in fp.parts):
                continue
            if "old" in [p.lower() for p in fp.parts]:
                continue
            rel = fp.relative_to(repo_path)
            vendor = rel.parts[0].lower() if len(rel.parts) > 1 else "misc"
            try:
                if fp.stat().st_size > 500:
                    prompt_files.append((fp, vendor))
            except OSError:
                pass
    
    seen = set()
    unique = []
    for fp, v in prompt_files:
        if fp not in seen:
            seen.add(fp)
            unique.append((fp, v))
    return unique


def extract_xml_tags(content: str) -> list[str]:
    """Extract all XML-style tags from content."""
    # Match opening XML tags like <identity>, <thinking>, etc.
    tags = re.findall(r'<([a-zA-Z_][\w-]*)(?:\s[^>]*)?>(?![\s\S]*<\1>)', content)
    # Also match self-closing tags
    self_closing = re.findall(r'<([a-zA-Z_][\w-]*)\s*/>', content)
    
    # Simpler approach: find all unique opening tags
    all_tags = re.findall(r'<(/?)([a-zA-Z_][\w-]*)[^>]*>', content)
    opening_tags = [tag for close, tag in all_tags if not close]
    
    return list(set(opening_tags))


def extract_markdown_sections(content: str) -> list[str]:
    """Extract markdown heading sections."""
    headings = re.findall(r'^#{1,4}\s+(.+)$', content, re.MULTILINE)
    return headings


def analyze_structure(content: str) -> dict:
    """Analyze structural patterns in a prompt."""
    analysis = {
        "word_count": len(content.split()),
        "char_count": len(content),
        "line_count": content.count('\n') + 1,
        "uses_xml": bool(re.search(r'<[a-zA-Z_][\w-]*>', content)),
        "uses_markdown_headers": bool(re.search(r'^#{1,4}\s+', content, re.MULTILINE)),
        "uses_numbered_list": bool(re.search(r'^\d+\.\s', content, re.MULTILINE)),
        "uses_bullet_list": bool(re.search(r'^[-*]\s', content, re.MULTILINE)),
        "uses_code_blocks": '```' in content,
        "uses_json_examples": bool(re.search(r'\{[\s\S]*"[\w]+"', content)),
        "uses_tool_definitions": any(kw in content.lower() for kw in ['function', 'tool_use', 'tool_call', 'tool_result']),
        "has_safety_section": any(kw in content.lower() for kw in ['safety', 'harmful', 'prohibited', 'not allowed']),
        "has_identity_section": any(kw in content.lower() for kw in ['you are', 'your name is', 'identity', 'persona']),
        "has_thinking_section": any(kw in content.lower() for kw in ['thinking', 'reasoning', 'chain of thought', 'step by step']),
    }
    
    return analysis


def analyze_all(repo_path: Path) -> dict:
    """Analyze all prompts and generate comprehensive report."""
    
    files = find_prompt_files(repo_path)
    print(f"Found {len(files)} prompt files")
    
    # Data collectors
    vendor_stats = defaultdict(lambda: {
        "count": 0,
        "total_words": 0,
        "total_chars": 0,
        "xml_tags": Counter(),
        "md_sections": Counter(),
        "structure_features": Counter(),
        "files": [],
    })
    
    all_xml_tags = Counter()
    all_md_sections = Counter()
    all_structure_features = Counter()
    
    for fp, vendor in files:
        try:
            content = fp.read_text(encoding="utf-8", errors="ignore")
            if len(content.strip()) < 100:
                continue
            
            size_kb = len(content.encode('utf-8')) / 1024
            
            # Extract patterns
            xml_tags = extract_xml_tags(content)
            md_sections = extract_markdown_sections(content)
            structure = analyze_structure(content)
            
            # Update vendor stats
            vs = vendor_stats[vendor]
            vs["count"] += 1
            vs["total_words"] += structure["word_count"]
            vs["total_chars"] += structure["char_count"]
            vs["files"].append({
                "name": fp.name,
                "size_kb": round(size_kb, 1),
                "word_count": structure["word_count"],
            })
            
            for tag in xml_tags:
                vs["xml_tags"][tag] += 1
                all_xml_tags[tag] += 1
            
            for section in md_sections:
                clean = section.strip().lower()[:60]
                vs["md_sections"][clean] += 1
                all_md_sections[clean] += 1
            
            for feature, value in structure.items():
                if isinstance(value, bool) and value:
                    vs["structure_features"][feature] += 1
                    all_structure_features[feature] += 1
            
            print(f"  [{vendor.upper()}] {fp.name}: {structure['word_count']} words, {len(xml_tags)} XML tags")
            
        except Exception as e:
            print(f"  [ERROR] {fp.name}: {e}")
    
    # Build report
    report = {
        "generated_at": __import__("datetime").datetime.now().isoformat(),
        "total_files": sum(vs["count"] for vs in vendor_stats.values()),
        "summary": {
            "top_xml_tags": dict(all_xml_tags.most_common(30)),
            "top_md_sections": dict(all_md_sections.most_common(20)),
            "structure_features": dict(all_structure_features.most_common(15)),
        },
        "vendor_profiles": {},
    }
    
    for vendor, vs in sorted(vendor_stats.items()):
        avg_words = vs["total_words"] // max(vs["count"], 1)
        avg_chars = vs["total_chars"] // max(vs["count"], 1)
        
        report["vendor_profiles"][vendor] = {
            "file_count": vs["count"],
            "avg_word_count": avg_words,
            "avg_char_count": avg_chars,
            "total_words": vs["total_words"],
            "uses_xml": vs["structure_features"].get("uses_xml", 0),
            "uses_markdown": vs["structure_features"].get("uses_markdown_headers", 0),
            "top_xml_tags": dict(vs["xml_tags"].most_common(15)),
            "top_md_sections": dict(vs["md_sections"].most_common(10)),
            "structure_features": dict(vs["structure_features"]),
            "files_by_size": sorted(vs["files"], key=lambda x: x["size_kb"], reverse=True)[:10],
        }
    
    return report


def main():
    script_dir = Path(__file__).parent
    repo_path = (script_dir / "../../system-prompts-reference").resolve()
    
    if not repo_path.exists():
        print(f"[ERROR] Repository not found: {repo_path}")
        return
    
    print(f"=== Prompt Pattern Analysis ===")
    print(f"Source: {repo_path}")
    print()
    
    report = analyze_all(repo_path)
    
    # Save report
    output_path = script_dir / "data" / "prompt_patterns.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n=== Report saved to {output_path} ===")
    print(f"\nTotal files analyzed: {report['total_files']}")
    
    print(f"\n--- Top XML Tags (across all vendors) ---")
    for tag, count in sorted(report["summary"]["top_xml_tags"].items(), key=lambda x: -x[1])[:15]:
        print(f"  <{tag}>: {count} prompts")
    
    print(f"\n--- Structure Features ---")
    for feature, count in sorted(report["summary"]["structure_features"].items(), key=lambda x: -x[1]):
        pct = (count / report["total_files"]) * 100
        print(f"  {feature}: {count}/{report['total_files']} ({pct:.0f}%)")
    
    print(f"\n--- Vendor Profiles ---")
    for vendor, profile in report["vendor_profiles"].items():
        print(f"\n  [{vendor.upper()}]")
        print(f"    Files: {profile['file_count']}")
        print(f"    Avg words: {profile['avg_word_count']}")
        print(f"    Uses XML: {profile['uses_xml']}/{profile['file_count']}")
        print(f"    Uses Markdown: {profile['uses_markdown']}/{profile['file_count']}")


if __name__ == "__main__":
    main()
