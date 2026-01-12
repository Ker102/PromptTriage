/**
 * Context7 MCP Integration Service
 * 
 * Provides live documentation lookup from Context7 for up-to-date
 * library/framework information when generating prompts.
 */

// Context7 library lookup result
export interface Context7Library {
    id: string;
    name: string;
    description: string;
    codeSnippets: number;
}

// Context7 documentation result
export interface Context7DocResult {
    content: string;
    source: string;
    relevance: number;
}

// Common libraries we might look up
export const LIBRARY_PATTERNS: Record<string, string> = {
    "next.js": "/vercel/next.js",
    "nextjs": "/vercel/next.js",
    "react": "/facebook/react",
    "langchain": "/langchain-ai/langchain",
    "langgraph": "/langchain-ai/langgraph",
    "supabase": "/supabase/supabase",
    "prisma": "/prisma/prisma",
    "tailwind": "/tailwindlabs/tailwindcss",
    "typescript": "/microsoft/typescript",
    "fastapi": "/tiangolo/fastapi",
    "anthropic": "/anthropics/anthropic-sdk-python",
    "openai": "/openai/openai-python",
    "gemini": "/google/generative-ai-js",
    "runway": "runway",
    "midjourney": "midjourney",
    "stable diffusion": "stable-diffusion",
};

/**
 * Detect libraries/frameworks mentioned in the prompt
 */
export function detectLibraries(text: string): string[] {
    const textLower = text.toLowerCase();
    const detected: string[] = [];

    for (const [pattern, libraryId] of Object.entries(LIBRARY_PATTERNS)) {
        if (textLower.includes(pattern)) {
            detected.push(libraryId);
        }
    }

    return [...new Set(detected)]; // Remove duplicates
}

/**
 * Check if the prompt likely needs live documentation
 */
export function needsLiveDocs(text: string): boolean {
    const textLower = text.toLowerCase();

    // Keywords that suggest needing current info
    const liveDataKeywords = [
        "latest",
        "current version",
        "up to date",
        "new features",
        "recent",
        "v19", "v18", "v15", "v14", // Version references
        "2025",
        "2026",
        "just released",
        "breaking changes",
    ];

    // Check for live data keywords
    const hasLiveKeyword = liveDataKeywords.some(kw => textLower.includes(kw));

    // Check for library mentions
    const hasLibrary = detectLibraries(text).length > 0;

    return hasLiveKeyword || hasLibrary;
}

/**
 * Format Context7 documentation for inclusion in prompts
 */
export function formatContext7Docs(docs: Context7DocResult[]): string {
    if (!docs.length) {
        return "";
    }

    const formatted = docs
        .map((doc, i) => {
            return `[Doc ${i + 1}] ${doc.source}\n${doc.content.slice(0, 1500)}`;
        })
        .join("\n\n---\n\n");

    return `<live_documentation>\n${formatted}\n</live_documentation>`;
}

/**
 * Build Context7 query based on detected libraries
 */
export function buildContext7Query(
    prompt: string,
    libraries: string[]
): { libraryId: string; query: string } | null {
    if (libraries.length === 0) {
        return null;
    }

    // Use the first detected library
    const libraryId = libraries[0];

    // Extract a focused query from the prompt
    // This is a simplified version - could be enhanced with LLM
    const queryWords = prompt
        .split(/\s+/)
        .filter(w => w.length > 3)
        .slice(0, 20)
        .join(" ");

    return {
        libraryId,
        query: queryWords
    };
}

/**
 * Note: The actual MCP calls would be made server-side.
 * This module provides utilities for detecting when to use Context7
 * and formatting the results.
 * 
 * Integration points:
 * 1. In analyze/route.ts: Call detectLibraries() and needsLiveDocs()
 * 2. If needed, make MCP call to Context7 server
 * 3. Include formatted docs in the prompt context
 * 
 * MCP calls (pseudo-code):
 * ```
 * // Resolve library ID
 * const library = await mcp_context7_resolve-library-id({ 
 *   libraryName: "next.js",
 *   query: "how to use app router" 
 * });
 * 
 * // Query documentation
 * const docs = await mcp_context7_query-docs({
 *   libraryId: library.id,
 *   query: "app router server components"
 * });
 * ```
 */
