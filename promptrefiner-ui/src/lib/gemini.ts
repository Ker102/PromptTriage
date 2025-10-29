import { GoogleGenerativeAI, GenerativeModel } from "@google/generative-ai";

const DEFAULT_MODEL = process.env.GEMINI_MODEL ?? "gemini-2.5-pro";

let cachedClient: GoogleGenerativeAI | null = null;
let cachedModel: GenerativeModel | null = null;

const missingKeyError =
  "Missing GOOGLE_GEMINI_API_KEY environment variable. Please add it to your .env.local file.";

export function getGeminiModel(modelName = DEFAULT_MODEL) {
  if (!process.env.GOOGLE_GEMINI_API_KEY) {
    throw new Error(missingKeyError);
  }

  if (!cachedClient) {
    cachedClient = new GoogleGenerativeAI(process.env.GOOGLE_GEMINI_API_KEY);
  }

  if (!cachedModel || cachedModel.model !== modelName) {
    cachedModel = cachedClient.getGenerativeModel({ model: modelName });
  }

  return cachedModel;
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
