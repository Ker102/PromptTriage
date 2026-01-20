/**
 * RAG Service Client for Frontend
 * 
 * Connects to the FastAPI backend for RAG queries (similar prompts from Pinecone)
 */

const RAG_BACKEND_URL = process.env.RAG_BACKEND_URL || "http://localhost:8000";

export interface RAGQueryResult {
    id: string;
    content: string;
    similarity: number;
    metadata: Record<string, string>;
}

export interface RAGQueryResponse {
    results: RAGQueryResult[];
    query: string;
    total_results: number;
    cache_hit?: boolean;
}

/**
 * Query the RAG backend for similar prompts
 */
export async function queryRAG(
    query: string,
    options: {
        topK?: number;
        category?: string;
        useCache?: boolean;
        modality?: string;  // text, image, video, system
    } = {}
): Promise<RAGQueryResponse> {
    const { topK = 5, category, useCache = true, modality = "text" } = options;

    try {
        const response = await fetch(`${RAG_BACKEND_URL}/api/rag/query`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                query,
                top_k: topK,
                category,
                use_cache: useCache,
                include_metadata: true,
                modality,  // Pass modality to backend for namespace routing
            }),
        });

        if (!response.ok) {
            throw new Error(`RAG query failed: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error("RAG query error:", error);
        // Return empty results on error (graceful degradation)
        return {
            results: [],
            query,
            total_results: 0,
        };
    }
}

/**
 * Check if RAG backend is available
 */
export async function isRAGAvailable(): Promise<boolean> {
    try {
        const response = await fetch(`${RAG_BACKEND_URL}/health`, {
            method: "GET",
        });
        return response.ok;
    } catch {
        return false;
    }
}

/**
 * Get RAG backend stats
 */
export async function getRAGStats(): Promise<Record<string, unknown> | null> {
    try {
        const response = await fetch(`${RAG_BACKEND_URL}/api/rag/stats`);
        if (response.ok) {
            return await response.json();
        }
        return null;
    } catch {
        return null;
    }
}

/**
 * Format RAG results as context for the analyzer
 */
export function formatRAGContext(results: RAGQueryResult[]): string {
    if (!results.length) return "";

    const formatted = results
        .map((result, index) => {
            const source = result.metadata?.source || "unknown";
            return `Example ${index + 1} (${source}, similarity: ${(result.similarity * 100).toFixed(1)}%):\n${result.content}`;
        })
        .join("\n\n");

    return `<similar_prompts>\nThe following are high-quality prompts similar to the user's request:\n\n${formatted}\n</similar_prompts>`;
}
