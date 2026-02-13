/**
 * Context7 MCP Integration Service
 *
 * Provides live documentation lookup by calling Context7's remote MCP server
 * at https://mcp.context7.com/mcp using JSON-RPC over HTTP (SSE transport).
 *
 * Two-step flow:
 * 1. resolve-library-id  →  maps a library name to a Context7 library ID
 * 2. query-docs           →  fetches relevant documentation for that library
 */

// ─── Interfaces ──────────────────────────────────────────────────────────────

export interface Context7Library {
    id: string;
    name: string;
    description: string;
    codeSnippets: number;
}

export interface Context7DocResult {
    content: string;
    source: string;
    relevance: number;
}

// ─── Library Detection ───────────────────────────────────────────────────────

/**
 * Common libraries and their Context7 IDs.
 * The key is a lowercase match pattern; the value is the Context7 library ID.
 */
export const LIBRARY_PATTERNS: Record<string, string> = {
    "next.js": "/vercel/next.js",
    nextjs: "/vercel/next.js",
    react: "/facebook/react",
    langchain: "/langchain-ai/langchain",
    langgraph: "/langchain-ai/langgraph",
    supabase: "/supabase/supabase",
    prisma: "/prisma/prisma",
    tailwind: "/tailwindlabs/tailwindcss",
    typescript: "/microsoft/typescript",
    fastapi: "/tiangolo/fastapi",
    anthropic: "/anthropics/anthropic-sdk-python",
    openai: "/openai/openai-python",
    gemini: "/google/generative-ai-js",
    express: "/expressjs/express",
    "vue.js": "/vuejs/core",
    vue: "/vuejs/core",
    svelte: "/sveltejs/svelte",
    django: "/django/django",
    flask: "/pallets/flask",
    pytorch: "/pytorch/pytorch",
    tensorflow: "/tensorflow/tensorflow",
    stripe: "/stripe/stripe-node",
    firebase: "/firebase/firebase-js-sdk",
    mongodb: "/mongodb/docs",
    drizzle: "/drizzle-team/drizzle-orm",
};

/**
 * Detect libraries/frameworks mentioned in the prompt text.
 */
export function detectLibraries(text: string): string[] {
    const textLower = text.toLowerCase();
    const detected: string[] = [];

    for (const [pattern, libraryId] of Object.entries(LIBRARY_PATTERNS)) {
        if (textLower.includes(pattern)) {
            detected.push(libraryId);
        }
    }

    return [...new Set(detected)];
}

/**
 * Simple heuristic: does this prompt look like it could benefit from live docs?
 */
export function needsLiveDocs(text: string): boolean {
    const textLower = text.toLowerCase();

    const liveDataKeywords = [
        "latest",
        "current version",
        "up to date",
        "new features",
        "recent",
        "v19", "v18", "v15", "v14",
        "2025", "2026",
        "just released",
        "breaking changes",
        "api",
        "documentation",
        "how to",
        "tutorial",
        "best practice",
    ];

    const hasLiveKeyword = liveDataKeywords.some((kw) => textLower.includes(kw));
    const hasLibrary = detectLibraries(text).length > 0;

    return hasLiveKeyword || hasLibrary;
}

// ─── Context7 MCP Client ────────────────────────────────────────────────────

const CONTEXT7_MCP_URL = "https://mcp.context7.com/mcp";

/**
 * Call a Context7 MCP tool via JSON-RPC over HTTP.
 *
 * Context7 uses Server-Sent Events (SSE) transport.
 * We send a JSON-RPC request and parse the SSE response for the result.
 */
async function callContext7Tool(
    toolName: string,
    args: Record<string, unknown>,
    timeoutMs = 10_000
): Promise<unknown> {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs);

    try {
        const response = await fetch(CONTEXT7_MCP_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Accept: "text/event-stream",
            },
            body: JSON.stringify({
                jsonrpc: "2.0",
                id: 1,
                method: "tools/call",
                params: {
                    name: toolName,
                    arguments: args,
                },
            }),
            signal: controller.signal,
        });

        if (!response.ok) {
            throw new Error(`Context7 HTTP ${response.status}: ${response.statusText}`);
        }

        // Parse SSE response: look for data lines containing JSON-RPC result
        const text = await response.text();

        // SSE format: lines like "data: {...}\n\n"
        const dataLines = text
            .split("\n")
            .filter((line) => line.startsWith("data: "))
            .map((line) => line.slice(6));

        for (const dataLine of dataLines) {
            try {
                const parsed = JSON.parse(dataLine);
                // JSON-RPC response contains "result"
                if (parsed.result) {
                    // MCP tool results come as { content: [{ type: "text", text: "..." }] }
                    const content = parsed.result?.content;
                    if (Array.isArray(content) && content.length > 0) {
                        return content[0].text ?? content[0];
                    }
                    return parsed.result;
                }
            } catch {
                // Not valid JSON, skip
            }
        }

        // Fallback: try parsing the whole response as JSON
        try {
            const directParsed = JSON.parse(text);
            if (directParsed.result) {
                const content = directParsed.result?.content;
                if (Array.isArray(content) && content.length > 0) {
                    return content[0].text ?? content[0];
                }
                return directParsed.result;
            }
        } catch {
            // Not JSON
        }

        return null;
    } finally {
        clearTimeout(timeout);
    }
}

/**
 * Resolve a library name to a Context7 library ID.
 */
export async function resolveLibraryId(
    libraryName: string,
    query: string
): Promise<string | null> {
    try {
        const result = await callContext7Tool("resolve-library-id", {
            libraryName,
            query,
        });

        if (typeof result === "string") {
            // Parse the result text to extract a library ID
            // The result typically contains a library ID like "/vercel/next.js"
            const idMatch = result.match(/\/[a-zA-Z0-9_-]+\/[a-zA-Z0-9._-]+/);
            return idMatch ? idMatch[0] : null;
        }

        return null;
    } catch (error) {
        console.error(`[Context7] resolveLibraryId failed for "${libraryName}":`, error);
        return null;
    }
}

/**
 * Query documentation for a specific library.
 */
export async function queryDocs(
    libraryId: string,
    query: string
): Promise<string | null> {
    try {
        const result = await callContext7Tool("query-docs", {
            libraryId,
            query,
        });

        if (typeof result === "string") {
            return result;
        }

        return null;
    } catch (error) {
        console.error(`[Context7] queryDocs failed for "${libraryId}":`, error);
        return null;
    }
}

/**
 * High-level: fetch live docs for detected libraries in a prompt.
 * Returns formatted documentation string or empty string.
 */
export async function fetchLiveDocsForPrompt(
    prompt: string
): Promise<{ docs: string; librariesQueried: string[] }> {
    const libraries = detectLibraries(prompt);

    if (libraries.length === 0) {
        return { docs: "", librariesQueried: [] };
    }

    // Limit to first 2 libraries to avoid excessive latency
    const toQuery = libraries.slice(0, 2);
    const results: string[] = [];
    const queriedLibs: string[] = [];

    for (const libraryId of toQuery) {
        try {
            // Build a focused query from the prompt
            const queryWords = prompt
                .split(/\s+/)
                .filter((w) => w.length > 3)
                .slice(0, 15)
                .join(" ");

            const docs = await queryDocs(libraryId, queryWords);

            if (docs && docs.length > 50) {
                results.push(`[${libraryId}]\n${docs.slice(0, 2000)}`);
                queriedLibs.push(libraryId);
            }
        } catch {
            // Skip failed queries
        }
    }

    if (results.length === 0) {
        return { docs: "", librariesQueried: queriedLibs };
    }

    const formatted = results.join("\n\n---\n\n");
    return {
        docs: `<live_documentation>\n${formatted}\n</live_documentation>`,
        librariesQueried: queriedLibs,
    };
}

/**
 * Format Context7 documentation for inclusion in prompts (legacy compat).
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
