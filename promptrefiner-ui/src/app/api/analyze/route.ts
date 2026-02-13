import { NextResponse } from "next/server";
import { PipelineLogger } from "@/lib/pipelineLogger";
import { getServerSession } from "next-auth";
import { getGeminiModel, extractJsonFromText } from "@/lib/gemini";
import type { Part } from "@google/generative-ai";
import type {
  AnalyzeRequestPayload,
  PromptAnalysisResult,
  PromptBlueprint,
  RetrievedDocument,
} from "@/types/prompt";
import {
  ANALYZER_FEW_SHOTS,
  ANALYZER_SYSTEM_PROMPT,
  FAST_MODE_SYSTEM_PROMPT,
  VIDEO_ANALYZER_SYSTEM_PROMPT,
  VIDEO_FAST_MODE_SYSTEM_PROMPT,
  IMAGE_ANALYZER_SYSTEM_PROMPT,
  IMAGE_FAST_MODE_SYSTEM_PROMPT,
  SYSTEM_PROMPT_ANALYZER,
  SYSTEM_PROMPT_FAST_MODE,
  PROMPT_VERSION,
} from "@/prompts/metaprompt";
import { searchFirecrawl } from "@/services/firecrawl";
import { queryRAG, formatRAGContext } from "@/services/rag";
import {
  needsLiveDocs,
  fetchLiveDocsForPrompt,
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

function validateAnalysisPayload(payload: PromptAnalysisResult, thinkingMode = false): string | null {
  if (!payload.analysis?.trim()) {
    return "Missing analysis text.";
  }

  if (!Array.isArray(payload.improvementAreas) || payload.improvementAreas.length === 0) {
    return "Improvement areas array is empty.";
  }

  // Only require questions in Thinking Mode
  if (thinkingMode) {
    if (!Array.isArray(payload.questions) || payload.questions.length < MIN_QUESTIONS) {
      return "Insufficient follow-up questions.";
    }

    for (const question of payload.questions) {
      if (!question.id || !question.question || !question.purpose) {
        return "Each question must include id, question, and purpose fields.";
      }
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
  const log = new PipelineLogger("ANALYZE");
  try {
    const session = await getServerSession(authOptions);

    // Secure development bypass: requires explicit flag AND localhost
    const allowDevBypass = process.env.ALLOW_DEV_BYPASS === "true";
    const isLocalhost = req.headers.get("host")?.includes("localhost") ?? false;
    const isDev = allowDevBypass && isLocalhost;
    const email = session?.user?.email ?? (isDev ? "dev@localhost" : null);

    log.step("AUTH", `user=${email ?? "NONE"}, isDev=${isDev}, plan=${isDev ? "PRO" : "FREE"}`);

    if (!email) {
      log.end("REJECTED — unauthenticated");
      return NextResponse.json(
        { error: "You must be signed in to analyze prompts." },
        { status: 401 },
      );
    }

    // Only grant PRO if explicit dev bypass is enabled
    const subscriptionPlan =
      (session?.user?.subscriptionPlan as string | undefined)?.toUpperCase() ??
      (isDev ? "PRO" : "FREE");

    const body = (await req.json()) as AnalyzeRequestPayload;
    const prompt = body.prompt?.trim();
    const rawTargetModel = body.targetModel?.trim();
    const context = body.context?.trim();
    const thinkingMode = body.thinkingMode ?? false;
    const desiredOutput = body.desiredOutput?.trim();
    const targetVendor = body.targetVendor?.trim(); // anthropic | openai | google

    log.step("INPUT", `prompt="${prompt?.slice(0, 80)}..." | model=${rawTargetModel} | modality=${body.modality} | thinkingMode=${thinkingMode} | desiredOutput=${desiredOutput ?? "none"} | vendor=${targetVendor ?? "auto"}`);

    // Validate modality - must be one of allowed values
    const VALID_MODALITIES = ["text", "image", "video", "system"] as const;
    const rawModality = body.modality ?? "text";
    if (!VALID_MODALITIES.includes(rawModality as typeof VALID_MODALITIES[number])) {
      return NextResponse.json(
        { error: `Invalid modality. Must be one of: ${VALID_MODALITIES.join(", ")}` },
        { status: 400 },
      );
    }
    const modality = rawModality as typeof VALID_MODALITIES[number];

    // Validate images array - ensure proper structure
    const rawImages = body.images ?? [];
    if (!Array.isArray(rawImages)) {
      return NextResponse.json(
        { error: "Images must be an array." },
        { status: 400 },
      );
    }
    const images = rawImages.filter((img): img is { base64: string; mimeType: string } =>
      typeof img === "object" &&
      img !== null &&
      typeof img.base64 === "string" &&
      typeof img.mimeType === "string"
    );

    // Debug-level logging (only in development or when debug flag is set)
    const isDebugMode = process.env.NODE_ENV !== "production" || process.env.DEBUG_LOGGING === "true";
    if (isDebugMode) {
      console.log("[DEBUG] Analyze request:", {
        modality,
        thinkingMode,
        targetVendor: targetVendor || "none",
        imagesCount: images.length,
        imageDetails: images.map((img, i) => ({
          index: i,
          mimeType: img.mimeType,
          base64Length: img.base64?.length ?? 0,
        })),
      });
    }

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

    const model = getGeminiModel(thinkingMode);
    log.decision("GEMINI_MODEL", thinkingMode ? "gemini-2.5-pro (thinking)" : "gemini-2.0-flash (fast)", thinkingMode ? "Thinking mode enabled — deeper multi-pass analysis" : "Fast mode — quick single-pass generation");

    try {
      recordUsageOrThrow(email, subscriptionPlan);
    } catch (usageError) {
      const message =
        usageError instanceof Error
          ? usageError.message
          : "Usage limit exceeded.";
      return NextResponse.json({ error: message }, { status: 429 });
    }

    // Query RAG for similar prompts (graceful degradation if backend unavailable)
    // Modality determines which Pinecone namespace to search:
    // - "video" -> video-prompts namespace
    // - "system" -> system-prompts namespace (via category filter)
    // - "text"/"image" -> default namespace
    let ragContext = "";
    try {
      const ragCategory = modality === "system" ? "system-prompts" : undefined;
      log.step("RAG_QUERY", `modality=${modality} | vendor=${targetVendor ?? "none"} | category=${ragCategory ?? "default"} | topK=3`);
      const ragResults = await queryRAG(prompt, {
        topK: 3,
        category: ragCategory,
        modality: modality,  // Pass modality for namespace routing
        targetVendor: targetVendor,  // Vendor-specific namespace routing
      });
      if (ragResults.results.length > 0) {
        ragContext = formatRAGContext(ragResults.results);
        log.step("RAG_RESULTS", `Found ${ragResults.results.length} similar prompts (top score: ${ragResults.results[0]?.similarity?.toFixed(3) ?? "?"})`);
      } else {
        log.skip("RAG_RESULTS", "No similar prompts found in corpus");
      }
    } catch (ragError) {
      log.error("RAG_QUERY", ragError);
      console.warn("RAG query failed, continuing without similar prompts:", ragError);
    }

    // Context7: Fetch live documentation for detected libraries via MCP
    let liveDocsContext = "";
    const combinedText = `${prompt} ${context ?? ""}`;
    if (needsLiveDocs(combinedText)) {
      try {
        log.step("CONTEXT7_DETECT", `Detected live docs need — querying Context7 MCP`);
        const { docs, librariesQueried } = await fetchLiveDocsForPrompt(combinedText);
        if (docs) {
          liveDocsContext = docs;
          log.step("CONTEXT7_RESULTS", `Retrieved docs for: ${librariesQueried.join(", ")}`);
        } else {
          log.skip("CONTEXT7_RESULTS", `Libraries detected but no docs returned (queried: ${librariesQueried.join(", ") || "none"})`);
        }
      } catch (context7Error) {
        log.error("CONTEXT7_QUERY", context7Error);
        console.warn("Context7 lookup failed, continuing without live docs:", context7Error);
      }
    } else {
      log.skip("CONTEXT7_DETECT", "No libraries or live-doc keywords detected");
    }

    const userPromptParts = [
      `<target_model>${targetModel}</target_model>`,
      `<original_prompt>${prompt}</original_prompt>`,
      `<extra_context>${context ?? ""}</extra_context>`,
    ];

    // Add desired output format instruction for the target model
    if (desiredOutput && (modality === "text" || modality === "system")) {
      userPromptParts.push(
        `<desired_output_format>The refined prompt MUST specify that the target AI should output its response in: ${desiredOutput}</desired_output_format>`
      );
      log.step("DESIRED_OUTPUT", `Injected: ${desiredOutput}`);
    } else if (desiredOutput) {
      log.skip("DESIRED_OUTPUT", `desiredOutput="${desiredOutput}" but modality=${modality} (only text/system supported)`);
    } else {
      log.skip("DESIRED_OUTPUT", "No desired output format selected");
    }

    // Add vendor-specific styling conventions when a target vendor is selected
    if (targetVendor && (modality === "text" || modality === "system")) {
      const vendorConventions: Record<string, string> = {
        anthropic: `Structure the prompt using XML tags (e.g., <identity>, <rules>, <thinking>, <output_format>). Use detailed identity blocks. Include chain-of-thought and safety sections. Anthropic prompts average ~8,000 words and heavily use XML-based section organization.`,
        openai: `Structure the prompt using Markdown headers (## sections). Use concise, declarative language. Include tool/function schemas when relevant. OpenAI prompts average ~1,400 words, rely on numbered lists and bullet points, and rarely use XML.`,
        google: `Use a hybrid XML/Markdown format. Include grounding instructions and multimodal considerations. Google prompts average ~1,300 words and balance structured sections with concise instructions.`,
      };
      const convention = vendorConventions[targetVendor];
      if (convention) {
        userPromptParts.push(
          `<vendor_style_guide>Target vendor: ${targetVendor.toUpperCase()}. ${convention}</vendor_style_guide>`
        );
        log.step("VENDOR_STYLE", `Injected ${targetVendor.toUpperCase()} style conventions`);
      }
    } else {
      log.skip("VENDOR_STYLE", targetVendor ? `modality=${modality} not text/system` : "No vendor derived from model");
    }

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

    // Select base system prompt based on modality
    type Modality = typeof VALID_MODALITIES[number];
    const getBaseSystemPrompt = (mod: Modality, thinking: boolean): string => {
      if (mod === "video") {
        return thinking ? VIDEO_ANALYZER_SYSTEM_PROMPT : VIDEO_FAST_MODE_SYSTEM_PROMPT;
      }
      if (mod === "image") {
        return thinking ? IMAGE_ANALYZER_SYSTEM_PROMPT : IMAGE_FAST_MODE_SYSTEM_PROMPT;
      }
      if (mod === "system") {
        return thinking ? SYSTEM_PROMPT_ANALYZER : SYSTEM_PROMPT_FAST_MODE;
      }
      // Default: text modality
      return thinking ? ANALYZER_SYSTEM_PROMPT : FAST_MODE_SYSTEM_PROMPT;
    };

    const basePrompt = getBaseSystemPrompt(modality, thinkingMode);
    const promptLabel = modality === "video" ? "VIDEO" : modality === "image" ? "IMAGE" : modality === "system" ? "SYSTEM" : "TEXT";
    log.decision("SYSTEM_PROMPT", `${promptLabel}_${thinkingMode ? "THINKING" : "FAST"}_MODE`, `modality=${modality}, thinkingMode=${thinkingMode}`);
    log.step("PROMPT_ASSEMBLY", `Parts: target_model + original_prompt + context${desiredOutput ? " + desired_output" : ""}${targetVendor ? " + vendor_style" : ""}${ragContext ? " + rag_context" : ""}${liveDocsContext ? " + context7_docs" : ""}${externalContext.length ? " + web_search" : ""}`);

    // Add thinking mode enhancements for deeper analysis
    const systemPrompt = thinkingMode
      ? `${basePrompt}

<thinking_mode_instructions>
You are in THINKING MODE - perform deeper, multi-pass analysis:
1. First, analyze the prompt thoroughly
2. Then, critique your own analysis - what did you miss?
3. Refine your questions to be more specific and actionable
4. Generate more comprehensive improvement areas
5. Ensure the blueprint is exceptionally detailed
</thinking_mode_instructions>`
      : basePrompt;

    // Adjust generation parameters based on mode
    const generationConfig = {
      temperature: thinkingMode ? 0.3 : 0.4, // Lower temp for more focused thinking
      topP: thinkingMode ? 0.85 : 0.9,
      responseMimeType: "application/json" as const,
    };

    // Build user message parts (text + optional images)
    const userParts: Part[] = [
      { text: userPrompt }
    ];

    // Add images to the request if provided (for multimodal analysis)
    if (images.length > 0) {
      console.log("📸 Adding", images.length, "image(s) to Gemini model request");
      for (const img of images) {
        userParts.push({
          inlineData: {
            data: img.base64,
            mimeType: img.mimeType,
          },
        });
      }
      console.log("📸 Images added successfully - model will analyze them");
    }

    log.step("GENERATING", `Sending to Gemini (temp=${generationConfig.temperature}, topP=${generationConfig.topP}, fewShots=${fewShotMessages.length / 2}, images=${images.length})`);
    const result = await model.generateContent({
      systemInstruction: {
        role: "system",
        parts: [{ text: systemPrompt }],
      },
      contents: [
        ...fewShotMessages,
        {
          role: "user",
          parts: userParts,
        },
      ],
      generationConfig,
    });

    const rawText = result.response.text();
    const parsed = extractJsonFromText<PromptAnalysisResult>(rawText);
    const validationError = validateAnalysisPayload(parsed, thinkingMode);

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

    log.step("RESPONSE", `Questions: ${enriched.questions?.length ?? 0}, Blueprint sections: ${Object.keys(enriched.blueprint ?? {}).length}, Confidence: ${enriched.overallConfidence?.slice(0, 50)}...`);
    log.end("SUCCESS");
    return NextResponse.json(enriched);
  } catch (error) {
    log.error("PIPELINE_FAILURE", error);
    log.end("FAILED");
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
