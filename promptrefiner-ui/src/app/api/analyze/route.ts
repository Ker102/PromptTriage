import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { getGeminiModel, extractJsonFromText } from "@/lib/gemini";
import type {
  AnalyzeRequestPayload,
  PromptAnalysisResult,
  PromptBlueprint,
  RetrievedDocument,
} from "@/types/prompt";
import {
  ANALYZER_FEW_SHOTS,
  ANALYZER_SYSTEM_PROMPT,
  PROMPT_VERSION,
} from "@/prompts/metaprompt";
import { searchFirecrawl } from "@/services/firecrawl";
import { queryRAG, formatRAGContext } from "@/services/rag";
import {
  detectLibraries,
  needsLiveDocs,
  buildContext7Query,
  formatContext7Docs,
  Context7DocResult,
} from "@/services/context7";
import { authOptions } from "@/auth";
import {
  isFirecrawlAvailable,
  recordUsageOrThrow,
} from "@/services/usage-limit";

const MIN_QUESTIONS = 2;
const MAX_SEARCH_QUERY_LENGTH = 512;

function validateBlueprint(blueprint: PromptBlueprint): string | null {
  if (!blueprint) {
    return "Blueprint is missing.";
  }

  if (blueprint.version !== PROMPT_VERSION) {
    return `Unexpected blueprint version: ${blueprint.version}`;
  }

  const requiredStringFields: Array<keyof PromptBlueprint> = [
    "intent",
    "audience",
    "tone",
    "outputFormat",
  ];

  for (const field of requiredStringFields) {
    const value = blueprint[field];
    if (typeof value !== "string" || !value.trim()) {
      return `Blueprint field '${field}' is empty.`;
    }
  }

  const requiredArrayFields: Array<keyof PromptBlueprint> = [
    "successCriteria",
    "requiredInputs",
    "domainContext",
    "constraints",
    "risks",
    "evaluationChecklist",
  ];

  for (const field of requiredArrayFields) {
    const value = blueprint[field];
    if (!Array.isArray(value) || value.length === 0) {
      return `Blueprint array field '${field}' is empty.`;
    }
  }

  return null;
}

function validateAnalysisPayload(payload: PromptAnalysisResult): string | null {
  if (!payload.analysis?.trim()) {
    return "Missing analysis text.";
  }

  if (!Array.isArray(payload.improvementAreas) || payload.improvementAreas.length === 0) {
    return "Improvement areas array is empty.";
  }

  if (!Array.isArray(payload.questions) || payload.questions.length < MIN_QUESTIONS) {
    return "Insufficient follow-up questions.";
  }

  for (const question of payload.questions) {
    if (!question.id || !question.question || !question.purpose) {
      return "Each question must include id, question, and purpose fields.";
    }
  }

  if (!payload.overallConfidence?.trim()) {
    return "Missing overall confidence message.";
  }

  const blueprintError = validateBlueprint(payload.blueprint);
  if (blueprintError) {
    return blueprintError;
  }

  return null;
}

export async function POST(req: Request) {
  try {
    const session = await getServerSession(authOptions);

    // In development, allow unauthenticated access
    const isDev = process.env.NODE_ENV === "development";
    const email = session?.user?.email ?? (isDev ? "dev@localhost" : null);

    if (!email && !isDev) {
      return NextResponse.json(
        { error: "You must be signed in to analyze prompts." },
        { status: 401 },
      );
    }

    const subscriptionPlan =
      (session?.user?.subscriptionPlan as string | undefined)?.toUpperCase() ??
      (isDev ? "PRO" : "FREE"); // Default to PRO in dev for testing

    const body = (await req.json()) as AnalyzeRequestPayload;
    const prompt = body.prompt?.trim();
    const rawTargetModel = body.targetModel?.trim();
    const context = body.context?.trim();

    if (!prompt) {
      return NextResponse.json(
        { error: "Prompt text is required." },
        { status: 400 },
      );
    }

    if (!rawTargetModel) {
      return NextResponse.json(
        { error: "Target model is required so we can tailor the refinement." },
        { status: 400 },
      );
    }

    const targetModel =
      rawTargetModel.toLowerCase() === "none / not sure yet"
        ? "Not specified yet"
        : rawTargetModel;

    let externalContext: RetrievedDocument[] = [];
    let externalContextError: string | undefined;
    if (body.useWebSearch) {
      if (!isFirecrawlAvailable(subscriptionPlan)) {
        return NextResponse.json(
          {
            error:
              "Web search is available on paid plans. Upgrade to access Firecrawl enrichment.",
          },
          { status: 403 },
        );
      }

      try {
        const query = buildSearchQuery(prompt, context);
        if (query) {
          externalContext = await searchFirecrawl(query, { limit: 5 });
        }
      } catch (searchError) {
        const message =
          searchError instanceof Error
            ? searchError.message
            : "Web search failed unexpectedly.";
        externalContextError = `Unable to retrieve supporting context: ${message}`;
        externalContext = [];
      }
    }

    const model = getGeminiModel();

    try {
      recordUsageOrThrow(email ?? "dev@localhost", subscriptionPlan);
    } catch (usageError) {
      const message =
        usageError instanceof Error
          ? usageError.message
          : "Usage limit exceeded.";
      return NextResponse.json({ error: message }, { status: 429 });
    }

    // Query RAG for similar prompts (graceful degradation if backend unavailable)
    let ragContext = "";
    try {
      const ragResults = await queryRAG(prompt, { topK: 3 });
      if (ragResults.results.length > 0) {
        ragContext = formatRAGContext(ragResults.results);
      }
    } catch (ragError) {
      console.warn("RAG query failed, continuing without similar prompts:", ragError);
    }

    // Context7: Detect libraries and fetch live documentation
    let liveDocsContext = "";
    const combinedText = `${prompt} ${context ?? ""}`;
    if (needsLiveDocs(combinedText)) {
      const detectedLibraries = detectLibraries(combinedText);
      if (detectedLibraries.length > 0) {
        const context7Query = buildContext7Query(prompt, detectedLibraries);
        if (context7Query) {
          try {
            // Make MCP call to Context7 for live documentation
            const context7Url = process.env.CONTEXT7_API_URL || "http://localhost:3100";
            const docsResponse = await fetch(`${context7Url}/api/docs`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                libraryId: context7Query.libraryId,
                query: context7Query.query,
              }),
            });

            if (docsResponse.ok) {
              const docs: Context7DocResult[] = await docsResponse.json();
              liveDocsContext = formatContext7Docs(docs);
              console.log(`Context7: Retrieved ${docs.length} docs for ${context7Query.libraryId}`);
            }
          } catch (context7Error) {
            console.warn("Context7 lookup failed, continuing without live docs:", context7Error);
          }
        }
      }
    }

    const userPromptParts = [
      `<target_model>${targetModel}</target_model>`,
      `<original_prompt>${prompt}</original_prompt>`,
      `<extra_context>${context ?? ""}</extra_context>`,
    ];

    // Add RAG context (similar prompts from our corpus)
    if (ragContext) {
      userPromptParts.push(ragContext);
    }

    // Add Context7 live documentation
    if (liveDocsContext) {
      userPromptParts.push(liveDocsContext);
    }

    if (externalContext.length) {
      userPromptParts.push(formatExternalContext(externalContext));
    }

    const userPrompt = userPromptParts.join("\n");

    const fewShotMessages = ANALYZER_FEW_SHOTS.flatMap(({ user, assistant }) => [
      { role: "user" as const, parts: [{ text: user }] },
      { role: "model" as const, parts: [{ text: assistant }] },
    ]);

    // Extract thinkingMode from request
    const thinkingMode = body.thinkingMode ?? false;

    // Enhance system prompt for Thinking Mode
    const systemPrompt = thinkingMode
      ? `${ANALYZER_SYSTEM_PROMPT}

<thinking_mode_instructions>
You are in THINKING MODE - perform deeper, multi-pass analysis:
1. First, analyze the prompt thoroughly
2. Then, critique your own analysis - what did you miss?
3. Refine your questions to be more specific and actionable
4. Generate more comprehensive improvement areas
5. Ensure the blueprint is exceptionally detailed
</thinking_mode_instructions>`
      : ANALYZER_SYSTEM_PROMPT;

    // Adjust generation parameters based on mode
    const generationConfig = {
      temperature: thinkingMode ? 0.3 : 0.4, // Lower temp for more focused thinking
      topP: thinkingMode ? 0.85 : 0.9,
      responseMimeType: "application/json" as const,
    };

    const result = await model.generateContent({
      systemInstruction: {
        role: "system",
        parts: [{ text: systemPrompt }],
      },
      contents: [
        ...fewShotMessages,
        {
          role: "user",
          parts: [{ text: userPrompt }],
        },
      ],
      generationConfig,
    });

    const rawText = result.response.text();
    const parsed = extractJsonFromText<PromptAnalysisResult>(rawText);
    const validationError = validateAnalysisPayload(parsed);

    if (validationError) {
      return NextResponse.json(
        { error: `Invalid analysis response: ${validationError}` },
        { status: 502 },
      );
    }

    const enriched: PromptAnalysisResult = {
      ...parsed,
      externalContext: externalContext.length ? externalContext : parsed.externalContext,
      externalContextError:
        externalContextError ?? parsed.externalContextError,
    };

    return NextResponse.json(enriched);
  } catch (error) {
    if (error instanceof SyntaxError) {
      return NextResponse.json(
        {
          error:
            "Failed to interpret the model output. Please try again or adjust your prompt.",
        },
        { status: 502 },
      );
    }

    const message =
      error instanceof Error ? error.message : "Unknown error occurred.";

    return NextResponse.json(
      { error: `Prompt analysis failed: ${message}` },
      { status: 500 },
    );
  }
}

function buildSearchQuery(prompt: string, context?: string | null): string {
  const combined = [context, prompt].filter(Boolean).join(" ").trim();
  if (!combined) {
    return "";
  }
  if (combined.length <= MAX_SEARCH_QUERY_LENGTH) {
    return combined;
  }
  return combined.slice(0, MAX_SEARCH_QUERY_LENGTH);
}

function formatExternalContext(documents: RetrievedDocument[]): string {
  const formatted = documents
    .map((doc, index) => {
      const position = index + 1;
      const snippet = doc.snippet.replace(/\s+/g, " ").trim();
      return `Result ${position}:\nTitle: ${doc.title}\nURL: ${doc.url}\nSummary: ${snippet}`;
    })
    .join("\n\n");

  return `<external_context>\n${formatted}\n</external_context>`;
}
