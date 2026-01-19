import { GoogleGenerativeAI, GenerativeModel } from "@google/generative-ai";

// Gemini 3 model variants
export const GEMINI_MODELS = {
  fast: "gemini-3-fast-preview",      // Fast Mode: quick, single-pass
  thinking: "gemini-3-pro-preview",   // Thinking Mode: deep, iterative
} as const;

const DEFAULT_MODEL = GEMINI_MODELS.fast;

let cachedClient: GoogleGenerativeAI | null = null;
const modelCache = new Map<string, GenerativeModel>();

const missingKeyError =
  "Missing GOOGLE_GEMINI_API_KEY environment variable. Please add it to your .env.local file.";

export function getGeminiModel(thinkingMode = false): GenerativeModel {
  const modelName = thinkingMode ? GEMINI_MODELS.thinking : GEMINI_MODELS.fast;
  if (!process.env.GOOGLE_GEMINI_API_KEY) {
    throw new Error(missingKeyError);
  }

  if (!cachedClient) {
    cachedClient = new GoogleGenerativeAI(process.env.GOOGLE_GEMINI_API_KEY);
  }

  // Use cached model if available, otherwise create new one
  if (!modelCache.has(modelName)) {
    modelCache.set(modelName, cachedClient.getGenerativeModel({ model: modelName }));
  }

  return modelCache.get(modelName)!;
}

export function extractJsonFromText<T>(rawText: string): T {
  const cleaned = rawText
    .trim()
    .replace(/^```json\s*/i, "")
    .replace(/^```\s*/i, "")
    .replace(/```$/i, "")
    .trim();

  return JSON.parse(cleaned) as T;
}
