import type { RetrievedDocument } from "@/types/prompt";

const DEFAULT_BASE_URL = "https://api.firecrawl.dev/v1";

interface FirecrawlSearchResult {
  title?: string;
  url?: string;
  snippet?: string;
  content?: string;
  description?: string;
  score?: number;
}

interface FirecrawlSearchResponse {
  results?: FirecrawlSearchResult[];
  data?: { results?: FirecrawlSearchResult[] };
}

export interface FirecrawlSearchOptions {
  limit?: number;
}

export async function searchFirecrawl(
  query: string,
  options: FirecrawlSearchOptions = {},
): Promise<RetrievedDocument[]> {
  const apiKey = process.env.FIRECRAWL_API_KEY;
  if (!apiKey) {
    throw new Error(
      "Missing FIRECRAWL_API_KEY environment variable. Add it to your .env.local file to enable web search.",
    );
  }

  const baseUrl = process.env.FIRECRAWL_API_URL ?? DEFAULT_BASE_URL;
  const limit = options.limit ?? 3;

  const response = await fetch(`${baseUrl}/search`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      query,
      page: 1,
      limit,
    }),
    cache: "no-store",
  });

  if (!response.ok) {
    const errorBody = await safeJson(response);
    const message =
      errorBody?.error ||
      errorBody?.message ||
      `Firecrawl search failed with status ${response.status}`;
    throw new Error(message);
  }

  const payload = (await response.json()) as FirecrawlSearchResponse;
  const rawResults =
    payload.results ?? payload.data?.results ?? [];

  return rawResults
    .filter((result): result is FirecrawlSearchResult => Boolean(result?.url || result?.title))
    .map((result) => ({
      title: result.title?.trim() || fallbackTitleFromUrl(result.url),
      url: result.url ?? "",
      snippet:
        result.snippet?.trim() ??
        result.description?.trim() ??
        truncate(result.content ?? "", 320),
      score: typeof result.score === "number" ? result.score : undefined,
    }))
    .filter((result) => Boolean(result.url && result.snippet));
}

function fallbackTitleFromUrl(url?: string): string {
  if (!url) {
    return "Untitled result";
  }
  try {
    const parsed = new URL(url);
    return parsed.hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

function truncate(text: string, maxLength: number): string {
  if (!text) {
    return "";
  }
  if (text.length <= maxLength) {
    return text;
  }
  return `${text.slice(0, maxLength - 1)}…`;
}

async function safeJson(response: Response) {
  try {
    return await response.json();
  } catch {
    return null;
  }
}
