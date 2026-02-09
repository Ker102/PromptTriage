#!/usr/bin/env python3
"""
Test Suite for PromptTriage Research Experiment

30 test prompts across 3 categories × 3 vendors = complete coverage matrix.
Each prompt represents a realistic user request for system prompt generation.
"""

from dataclasses import dataclass, field
from typing import Literal

Vendor = Literal["anthropic", "openai", "google"]
Category = Literal["coding", "business", "creative"]


@dataclass
class TestPrompt:
    """A single test case for the benchmark."""
    id: str
    category: Category
    target_vendor: Vendor
    user_prompt: str
    context: str = ""
    target_model: str = ""
    difficulty: Literal["easy", "medium", "hard"] = "medium"


# =============================================================================
# Category 1: Coding Assistants (10 prompts)
# =============================================================================

CODING_PROMPTS = [
    TestPrompt(
        id="code-01",
        category="coding",
        target_vendor="anthropic",
        user_prompt="Build me a Python debugging assistant that helps find and fix bugs in my code",
        target_model="Claude Sonnet 4",
        difficulty="medium",
    ),
    TestPrompt(
        id="code-02",
        category="coding",
        target_vendor="openai",
        user_prompt="I need a code reviewer that checks for security vulnerabilities and suggests fixes",
        target_model="GPT-5.2",
        difficulty="hard",
    ),
    TestPrompt(
        id="code-03",
        category="coding",
        target_vendor="google",
        user_prompt="Create an AI pair programmer that helps me write TypeScript React components",
        target_model="Gemini 3 Pro",
        difficulty="medium",
    ),
    TestPrompt(
        id="code-04",
        category="coding",
        target_vendor="anthropic",
        user_prompt="Design a CI/CD pipeline assistant that writes GitHub Actions workflows and troubleshoots deployment failures",
        context="We use a monorepo with Next.js frontend and FastAPI backend",
        target_model="Claude Sonnet 4",
        difficulty="hard",
    ),
    TestPrompt(
        id="code-05",
        category="coding",
        target_vendor="openai",
        user_prompt="Make a SQL query optimizer that rewrites slow queries and explains the optimization",
        target_model="GPT-5.2",
        difficulty="medium",
    ),
    TestPrompt(
        id="code-06",
        category="coding",
        target_vendor="google",
        user_prompt="Build a documentation generator that reads code and creates API docs",
        target_model="Gemini 3 Flash",
        difficulty="easy",
    ),
    TestPrompt(
        id="code-07",
        category="coding",
        target_vendor="anthropic",
        user_prompt="Create an AI that converts legacy Python 2 code to modern Python 3.12+",
        context="The codebase is 50K lines with heavy use of print statements and old-style string formatting",
        target_model="Claude Opus 4.6",
        difficulty="hard",
    ),
    TestPrompt(
        id="code-08",
        category="coding",
        target_vendor="openai",
        user_prompt="Design a terminal command assistant that helps with complex bash/powershell operations",
        target_model="GPT-4.1",
        difficulty="easy",
    ),
    TestPrompt(
        id="code-09",
        category="coding",
        target_vendor="google",
        user_prompt="Build me a test writing assistant that generates unit tests for existing functions",
        context="We use pytest with fixtures and mocks extensively",
        target_model="Gemini 3 Pro",
        difficulty="medium",
    ),
    TestPrompt(
        id="code-10",
        category="coding",
        target_vendor="anthropic",
        user_prompt="Create an architecture advisor that reviews system design documents and suggests improvements",
        context="Microservices on Kubernetes, event-driven with Kafka",
        target_model="Claude Sonnet 4",
        difficulty="hard",
    ),
]

# =============================================================================
# Category 2: Business Agents (10 prompts)
# =============================================================================

BUSINESS_PROMPTS = [
    TestPrompt(
        id="biz-01",
        category="business",
        target_vendor="anthropic",
        user_prompt="Build a customer support chatbot for a SaaS product that handles billing questions and feature requests",
        context="Product is a project management tool, 10K users, Stripe billing",
        target_model="Claude Sonnet 4",
        difficulty="medium",
    ),
    TestPrompt(
        id="biz-02",
        category="business",
        target_vendor="openai",
        user_prompt="Create a sales email generator that writes personalized outreach based on prospect data",
        target_model="GPT-5.2",
        difficulty="easy",
    ),
    TestPrompt(
        id="biz-03",
        category="business",
        target_vendor="google",
        user_prompt="Design a data analysis agent that generates insights from CSV files and creates summary reports",
        target_model="Gemini 3 Pro",
        difficulty="medium",
    ),
    TestPrompt(
        id="biz-04",
        category="business",
        target_vendor="anthropic",
        user_prompt="Build a legal document reviewer that identifies risks and compliance issues in contracts",
        context="Focus on EU GDPR and US data privacy regulations",
        target_model="Claude Opus 4.6",
        difficulty="hard",
    ),
    TestPrompt(
        id="biz-05",
        category="business",
        target_vendor="openai",
        user_prompt="Create a meeting summarizer that extracts action items, decisions, and follow-ups",
        target_model="GPT-4.1",
        difficulty="easy",
    ),
    TestPrompt(
        id="biz-06",
        category="business",
        target_vendor="google",
        user_prompt="Design an HR onboarding assistant that guides new employees through company processes",
        context="For a 200-person tech startup with remote-first culture",
        target_model="Gemini 3 Flash",
        difficulty="medium",
    ),
    TestPrompt(
        id="biz-07",
        category="business",
        target_vendor="anthropic",
        user_prompt="Build a competitive intelligence agent that monitors and analyzes competitor product launches",
        target_model="Claude Sonnet 4",
        difficulty="hard",
    ),
    TestPrompt(
        id="biz-08",
        category="business",
        target_vendor="openai",
        user_prompt="Create a financial planning assistant that helps small businesses with budgeting and forecasting",
        target_model="GPT-5.2",
        difficulty="medium",
    ),
    TestPrompt(
        id="biz-09",
        category="business",
        target_vendor="google",
        user_prompt="Design a recruitment screening assistant that evaluates resumes against job descriptions",
        context="Must avoid bias and comply with equal opportunity regulations",
        target_model="Gemini 3 Pro",
        difficulty="hard",
    ),
    TestPrompt(
        id="biz-10",
        category="business",
        target_vendor="anthropic",
        user_prompt="Build a project status reporter that creates weekly updates from Jira, GitHub, and Slack data",
        target_model="Claude Sonnet 4",
        difficulty="medium",
    ),
]

# =============================================================================
# Category 3: Creative Tools (10 prompts)
# =============================================================================

CREATIVE_PROMPTS = [
    TestPrompt(
        id="creative-01",
        category="creative",
        target_vendor="anthropic",
        user_prompt="Build a blog content writer that matches my brand voice and optimizes for SEO",
        context="Tech blog about AI and machine learning, casual but authoritative tone",
        target_model="Claude Sonnet 4",
        difficulty="medium",
    ),
    TestPrompt(
        id="creative-02",
        category="creative",
        target_vendor="openai",
        user_prompt="Create an image prompt generator for product photography using DALL-E and Midjourney",
        target_model="GPT-5.2",
        difficulty="medium",
    ),
    TestPrompt(
        id="creative-03",
        category="creative",
        target_vendor="google",
        user_prompt="Design an AI tutor that teaches programming through interactive exercises",
        context="Target audience: complete beginners learning Python",
        target_model="Gemini 3 Pro",
        difficulty="medium",
    ),
    TestPrompt(
        id="creative-04",
        category="creative",
        target_vendor="anthropic",
        user_prompt="Build a creative writing assistant that helps with novel plotting, character development, and dialogue",
        target_model="Claude Opus 4.6",
        difficulty="hard",
    ),
    TestPrompt(
        id="creative-05",
        category="creative",
        target_vendor="openai",
        user_prompt="Create a social media content planner that generates posts for LinkedIn, Twitter, and Instagram",
        target_model="GPT-4.1",
        difficulty="easy",
    ),
    TestPrompt(
        id="creative-06",
        category="creative",
        target_vendor="google",
        user_prompt="Design a video script writer for YouTube tech tutorials",
        context="10-15 minute videos, educational but entertaining, similar to Fireship style",
        target_model="Gemini 3 Pro",
        difficulty="medium",
    ),
    TestPrompt(
        id="creative-07",
        category="creative",
        target_vendor="anthropic",
        user_prompt="Build an email newsletter writer that creates engaging weekly digests from source material",
        target_model="Claude Sonnet 4",
        difficulty="easy",
    ),
    TestPrompt(
        id="creative-08",
        category="creative",
        target_vendor="openai",
        user_prompt="Create a brand naming assistant that generates creative product names with trademark availability checks",
        target_model="GPT-5.2",
        difficulty="medium",
    ),
    TestPrompt(
        id="creative-09",
        category="creative",
        target_vendor="google",
        user_prompt="Design a presentation builder that creates slide outlines and speaker notes from rough topics",
        target_model="Gemini 3 Flash",
        difficulty="easy",
    ),
    TestPrompt(
        id="creative-10",
        category="creative",
        target_vendor="anthropic",
        user_prompt="Build a UX copywriter that generates microcopy for web apps — buttons, tooltips, error messages, onboarding flows",
        context="Product is a developer tool, tone should be friendly but professional",
        target_model="Claude Sonnet 4",
        difficulty="hard",
    ),
]

# =============================================================================
# Combined test suite
# =============================================================================

ALL_TEST_PROMPTS = CODING_PROMPTS + BUSINESS_PROMPTS + CREATIVE_PROMPTS

# Convenience views
BY_CATEGORY: dict[str, list[TestPrompt]] = {
    "coding": CODING_PROMPTS,
    "business": BUSINESS_PROMPTS,
    "creative": CREATIVE_PROMPTS,
}

BY_VENDOR: dict[str, list[TestPrompt]] = {
    "anthropic": [p for p in ALL_TEST_PROMPTS if p.target_vendor == "anthropic"],
    "openai": [p for p in ALL_TEST_PROMPTS if p.target_vendor == "openai"],
    "google": [p for p in ALL_TEST_PROMPTS if p.target_vendor == "google"],
}

BY_DIFFICULTY: dict[str, list[TestPrompt]] = {
    "easy": [p for p in ALL_TEST_PROMPTS if p.difficulty == "easy"],
    "medium": [p for p in ALL_TEST_PROMPTS if p.difficulty == "medium"],
    "hard": [p for p in ALL_TEST_PROMPTS if p.difficulty == "hard"],
}


if __name__ == "__main__":
    print(f"Total test prompts: {len(ALL_TEST_PROMPTS)}")
    print(f"  By category: {', '.join(f'{k}={len(v)}' for k, v in BY_CATEGORY.items())}")
    print(f"  By vendor:   {', '.join(f'{k}={len(v)}' for k, v in BY_VENDOR.items())}")
    print(f"  By difficulty: {', '.join(f'{k}={len(v)}' for k, v in BY_DIFFICULTY.items())}")
