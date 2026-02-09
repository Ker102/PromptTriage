"""
6-Level RAG Strategy Benchmark for PromptTriage Research.

L0: No RAG        - Direct LLM generation, no retrieval
L1: Naive RAG     - Embed query -> top-K Pinecone -> inject
L2: Rerank RAG    - L1 + cross-encoder reranker (top-20 -> top-3)
L3: CRAG          - L2 + relevance evaluator + web fallback
L4: Judge RAG     - L3 + LLM grades each doc before injection
L5: Agentic RAG   - L4 + query decomposition + multi-step retrieval
"""

import os
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv
load_dotenv()


@dataclass
class RAGResult:
    """Result from a RAG retrieval step."""
    documents: list[dict]       # Retrieved docs with content + metadata
    method: str                 # Which RAG level was used
    retrieval_ms: int           # Time spent on retrieval
    num_retrieved: int          # How many docs initially retrieved
    num_after_filter: int       # How many passed filtering/reranking


# ── Shared Utilities ─────────────────────────────────────────────────────

def get_gemini_client():
    """Create a Gemini client for embeddings and generation."""
    from google import genai
    return genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))


def embed_query(client, text: str) -> list[float]:
    """Embed a query using Gemini embedding-001."""
    from google.genai import types
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=768,
        ),
    )
    return result.embeddings[0].values


def get_pinecone_index():
    """Get Pinecone index handle."""
    from pinecone import Pinecone
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    return pc.Index(os.getenv("PINECONE_INDEX_NAME", "prompttriage-prompts"))


def query_pinecone(index, embedding, top_k=5, namespace=""):
    """Query Pinecone and return formatted results."""
    results = index.query(
        vector=embedding, top_k=top_k,
        include_metadata=True, namespace=namespace,
    )
    docs = []
    for m in results.matches:
        docs.append({
            "id": m.id,
            "content": m.metadata.get("content", ""),
            "score": m.score,
            "metadata": {k: v for k, v in m.metadata.items() if k != "content"},
        })
    return docs


VENDOR_NS = {
    "anthropic": "system-prompts-anthropic",
    "openai": "system-prompts-openai",
    "google": "system-prompts-google",
}


# ── L0: No RAG ──────────────────────────────────────────────────────────

def no_rag(**kwargs) -> RAGResult:
    """No retrieval — baseline."""
    return RAGResult(documents=[], method="L0_no_rag",
                     retrieval_ms=0, num_retrieved=0, num_after_filter=0)


# ── L1: Naive RAG ───────────────────────────────────────────────────────

def naive_rag(query: str, vendor: str = "", top_k: int = 5) -> RAGResult:
    """Standard embedding search -> top-K."""
    t0 = time.time()
    client = get_gemini_client()
    index = get_pinecone_index()
    emb = embed_query(client, query)
    ns = VENDOR_NS.get(vendor, "")
    docs = query_pinecone(index, emb, top_k=top_k, namespace=ns)
    ms = int((time.time() - t0) * 1000)
    return RAGResult(documents=docs, method="L1_naive_rag",
                     retrieval_ms=ms, num_retrieved=len(docs),
                     num_after_filter=len(docs))


# ── L2: Rerank RAG ──────────────────────────────────────────────────────

def rerank_rag(query: str, vendor: str = "", top_k: int = 3,
               initial_k: int = 20) -> RAGResult:
    """Retrieve broadly, then rerank with cross-encoder."""
    t0 = time.time()
    client = get_gemini_client()
    index = get_pinecone_index()
    emb = embed_query(client, query)
    ns = VENDOR_NS.get(vendor, "")
    candidates = query_pinecone(index, emb, top_k=initial_k, namespace=ns)

    if not candidates:
        ms = int((time.time() - t0) * 1000)
        return RAGResult(documents=[], method="L2_rerank_rag",
                         retrieval_ms=ms, num_retrieved=0, num_after_filter=0)

    # Rerank using Gemini Flash as a lightweight scorer
    scored = _rerank_with_llm(client, query, candidates)
    scored.sort(key=lambda x: x["rerank_score"], reverse=True)
    final = scored[:top_k]

    ms = int((time.time() - t0) * 1000)
    return RAGResult(documents=final, method="L2_rerank_rag",
                     retrieval_ms=ms, num_retrieved=len(candidates),
                     num_after_filter=len(final))


def _rerank_with_llm(client, query: str, docs: list[dict]) -> list[dict]:
    """Use Gemini Flash to score relevance of each doc to query."""
    prompt = f"""Score how relevant each document is to this query on a 1-10 scale.
Query: "{query}"

Documents:
"""
    for i, d in enumerate(docs):
        snippet = d["content"][:300]
        prompt += f"\n[{i}] {snippet}\n"

    prompt += "\nRespond with JSON array of scores: [{\"index\": 0, \"score\": 8}, ...]"

    try:
        resp = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config={"temperature": 0.1, "response_mime_type": "application/json"},
        )
        scores = json.loads(resp.text)
        for item in scores:
            idx = item.get("index", 0)
            if 0 <= idx < len(docs):
                docs[idx]["rerank_score"] = item.get("score", 5)
    except Exception as e:
        print(f"  [Rerank] LLM scoring failed: {e}, using original scores")
        for d in docs:
            d["rerank_score"] = d.get("score", 0.5) * 10

    return docs


# ── L3: CRAG (Corrective RAG) ───────────────────────────────────────────

def corrective_rag(query: str, vendor: str = "", top_k: int = 3,
                   threshold: float = 5.0) -> RAGResult:
    """Rerank + relevance check. If docs score below threshold, try web."""
    t0 = time.time()
    reranked = rerank_rag(query, vendor, top_k=top_k, initial_k=20)

    # Check if top results are good enough
    good_docs = [d for d in reranked.documents
                 if d.get("rerank_score", 0) >= threshold]

    if len(good_docs) < 2:
        # Fallback: web search via Gemini grounding
        print("  [CRAG] Low confidence — attempting web fallback")
        web_docs = _web_fallback(query, vendor)
        good_docs = (good_docs + web_docs)[:top_k]

    ms = int((time.time() - t0) * 1000)
    return RAGResult(documents=good_docs, method="L3_corrective_rag",
                     retrieval_ms=ms,
                     num_retrieved=reranked.num_retrieved,
                     num_after_filter=len(good_docs))


def _web_fallback(query: str, vendor: str) -> list[dict]:
    """Use Gemini with grounding to find relevant context from the web."""
    client = get_gemini_client()
    search_query = f"best practices {vendor} system prompt structure examples"
    try:
        resp = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"Find 2-3 high-quality examples of {vendor} system prompts "
                     f"for this use case: {query}. "
                     f"Return the key structural patterns and conventions.",
            config={"temperature": 0.3},
        )
        return [{"id": "web-fallback", "content": resp.text,
                 "score": 0.7, "rerank_score": 7,
                 "metadata": {"source": "web_fallback"}}]
    except Exception as e:
        print(f"  [CRAG] Web fallback failed: {e}")
        return []


# ── L4: Judge RAG ────────────────────────────────────────────────────────

def judge_rag(query: str, vendor: str = "", top_k: int = 3) -> RAGResult:
    """CRAG + LLM judges each doc's usefulness before injection."""
    t0 = time.time()
    crag_result = corrective_rag(query, vendor, top_k=top_k + 2)

    if not crag_result.documents:
        ms = int((time.time() - t0) * 1000)
        return RAGResult(documents=[], method="L4_judge_rag",
                         retrieval_ms=ms, num_retrieved=0, num_after_filter=0)

    # Judge each document
    client = get_gemini_client()
    judged = []
    for doc in crag_result.documents:
        verdict = _judge_document(client, query, vendor, doc)
        if verdict["useful"]:
            doc["judge_reasoning"] = verdict["reasoning"]
            judged.append(doc)

    ms = int((time.time() - t0) * 1000)
    return RAGResult(documents=judged[:top_k], method="L4_judge_rag",
                     retrieval_ms=ms,
                     num_retrieved=crag_result.num_retrieved,
                     num_after_filter=len(judged))


def _judge_document(client, query: str, vendor: str, doc: dict) -> dict:
    """LLM evaluates whether a retrieved doc is useful for this query."""
    snippet = doc["content"][:500]
    prompt = f"""Is this document useful as a reference for generating a {vendor} system prompt?

User request: "{query}"
Document snippet: "{snippet}"

Respond JSON: {{"useful": true/false, "reasoning": "brief explanation"}}"""

    try:
        resp = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config={"temperature": 0.1, "response_mime_type": "application/json"},
        )
        return json.loads(resp.text)
    except Exception:
        return {"useful": True, "reasoning": "Judge failed, keeping doc"}


# ── L5: Agentic RAG ─────────────────────────────────────────────────────

def agentic_rag(query: str, vendor: str = "", top_k: int = 3) -> RAGResult:
    """Judge RAG + query decomposition + multi-step retrieval."""
    t0 = time.time()
    client = get_gemini_client()

    # Step 1: Decompose query into sub-queries
    sub_queries = _decompose_query(client, query, vendor)
    print(f"  [Agentic] Decomposed into {len(sub_queries)} sub-queries")

    # Step 2: Retrieve for each sub-query
    all_docs = {}
    for sq in sub_queries:
        result = judge_rag(sq, vendor, top_k=2)
        for doc in result.documents:
            if doc["id"] not in all_docs:
                all_docs[doc["id"]] = doc

    # Step 3: Self-reflection — are we missing anything?
    docs_list = list(all_docs.values())
    if len(docs_list) < top_k:
        print("  [Agentic] Insufficient docs, running reflection query")
        gap_query = _identify_gaps(client, query, vendor, docs_list)
        if gap_query:
            extra = judge_rag(gap_query, vendor, top_k=2)
            for doc in extra.documents:
                if doc["id"] not in all_docs:
                    all_docs[doc["id"]] = doc

    final = list(all_docs.values())[:top_k]
    ms = int((time.time() - t0) * 1000)
    return RAGResult(documents=final, method="L5_agentic_rag",
                     retrieval_ms=ms,
                     num_retrieved=len(all_docs),
                     num_after_filter=len(final))


def _decompose_query(client, query: str, vendor: str) -> list[str]:
    """Break user request into targeted sub-queries for retrieval."""
    prompt = f"""Break this system prompt request into 2-3 focused retrieval queries.

Request: "{query}"
Target vendor: {vendor}

Return JSON array of query strings:
["query about structure...", "query about safety...", "query about tools..."]"""

    try:
        resp = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config={"temperature": 0.3, "response_mime_type": "application/json"},
        )
        queries = json.loads(resp.text)
        return queries if isinstance(queries, list) else [query]
    except Exception:
        return [query]


def _identify_gaps(client, query: str, vendor: str,
                   docs: list[dict]) -> Optional[str]:
    """Check if retrieved docs are missing critical info, generate gap query."""
    snippets = "\n".join(d["content"][:200] for d in docs[:3])
    prompt = f"""Given this user request and the retrieved reference docs, 
is there a critical gap in the context?

Request: "{query}" (vendor: {vendor})
Retrieved docs summary: {snippets}

If there's a gap, return a JSON with a query to fill it:
{{"has_gap": true, "gap_query": "..."}}
If no gap: {{"has_gap": false}}"""

    try:
        resp = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config={"temperature": 0.2, "response_mime_type": "application/json"},
        )
        result = json.loads(resp.text)
        if result.get("has_gap"):
            return result.get("gap_query")
    except Exception:
        pass
    return None


# ── Registry ─────────────────────────────────────────────────────────────

RAG_METHODS = {
    "L0_no_rag": no_rag,
    "L1_naive_rag": naive_rag,
    "L2_rerank_rag": rerank_rag,
    "L3_corrective_rag": corrective_rag,
    "L4_judge_rag": judge_rag,
    "L5_agentic_rag": agentic_rag,
}


def run_rag_method(method_name: str, query: str, vendor: str = "",
                   top_k: int = 3) -> RAGResult:
    """Run a specific RAG method by name."""
    fn = RAG_METHODS.get(method_name)
    if not fn:
        raise ValueError(f"Unknown method: {method_name}")
    if method_name == "L0_no_rag":
        return fn()
    return fn(query=query, vendor=vendor, top_k=top_k)


if __name__ == "__main__":
    print("=== RAG Methods Test ===")
    for name in RAG_METHODS:
        print(f"  Registered: {name}")
    print(f"\nTotal methods: {len(RAG_METHODS)}")
