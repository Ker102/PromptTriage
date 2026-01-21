import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { getGeminiModel, extractJsonFromText } from "@/lib/gemini";
import type {
  PromptBlueprint,
  PromptRefinementResult,
  RefineRequestPayload,
  RetrievedDocument,
} from "@/types/prompt";
import {
  PROMPT_VERSION,
  REFINER_FEW_SHOTS,
  REFINER_SYSTEM_PROMPT,
  VIDEO_REFINER_SYSTEM_PROMPT,
  IMAGE_REFINER_SYSTEM_PROMPT,
  SYSTEM_PROMPT_REFINER,
} from "@/prompts/metaprompt";
import { authOptions } from "@/auth";
import {
  isFirecrawlAvailable,
  recordUsageOrThrow,
} from "@/services/usage-limit";

function validateBlueprintInput(blueprint: PromptBlueprint | undefined) {
  if (!blueprint) {
    throw new Error(
      "Blueprint from analysis is required before refining the prompt.",
    );
  }

  if (blueprint.version !== PROMPT_VERSION) {
    throw new Error(
      `Blueprint version mismatch. Expected ${PROMPT_VERSION}, received ${blueprint.version}.`,
    );
  }
}

function validateRefinementPayload(payload: PromptRefinementResult): string | null {
  if (!payload.refinedPrompt?.trim()) {
    return "Missing refined prompt text.";
  }

  if (!payload.guidance?.trim()) {
    return "Missing guidance message.";
  }

  if (!Array.isArray(payload.changeSummary) || payload.changeSummary.length === 0) {
    return "Change summary must include at least one item.";
  }

  if (!Array.isArray(payload.assumptions)) {
    return "Assumptions must be an array (can be empty).";
  }

  if (!Array.isArray(payload.evaluationCriteria) || payload.evaluationCriteria.length === 0) {
    return "Evaluation criteria must include at least one item.";
  }

  return null;
}

export async function POST(req: Request) {
  try {
    const session = await getServerSession(authOptions);

    // Secure development bypass: requires explicit flag AND localhost
    const allowDevBypass = process.env.ALLOW_DEV_BYPASS === "true";
    const isLocalhost = req.headers.get("host")?.includes("localhost") ?? false;
    const isDev = allowDevBypass && isLocalhost;
    const email = session?.user?.email ?? (isDev ? "dev@localhost" : null);

    if (!email) {
      return NextResponse.json(
        { error: "You must be signed in to refine prompts." },
        { status: 401 },
      );
    }

    // Only grant PRO if explicit dev bypass is enabled
    const subscriptionPlan =
      (session?.user?.subscriptionPlan as string | undefined)?.toUpperCase() ??
      (isDev ? "PRO" : "FREE");

    const body = (await req.json()) as RefineRequestPayload;
    const prompt = body.prompt?.trim();
    const rawTargetModel = body.targetModel?.trim();
    const context = body.context?.trim();
    const tone = body.tone?.trim();
    const outputFormats = body.outputFormats ?? [];
    const questions = body.questions ?? [];
    const answers = body.answers ?? {};
    const blueprint = body.blueprint;
    const externalContext = body.externalContext ?? [];
    const variationHint = body.variationHint?.trim();

    // Extract modality for prompt routing (defaults to text)
    const VALID_MODALITIES = ["text", "image", "video", "system"] as const;
    const rawModality = body.modality ?? "text";
    const modality = VALID_MODALITIES.includes(rawModality as typeof VALID_MODALITIES[number])
      ? (rawModality as typeof VALID_MODALITIES[number])
      : "text";

    if (!prompt) {
      return NextResponse.json(
        { error: "Prompt text is required." },
        { status: 400 },
      );
    }

    if (!rawTargetModel) {
      return NextResponse.json(
        { error: "Target model is required." },
        { status: 400 },
      );
    }

    const targetModel =
      rawTargetModel.toLowerCase() === "none / not sure yet"
        ? "Not specified yet"
        : rawTargetModel;

    if (!questions.length) {
      return NextResponse.json(
        {
          error:
            "Questions from the analysis phase are required to refine the prompt.",
        },
        { status: 400 },
      );
    }

    try {
      validateBlueprintInput(blueprint);
    } catch (validationError) {
      const message =
        validationError instanceof Error
          ? validationError.message
          : "Invalid blueprint.";
      return NextResponse.json({ error: message }, { status: 400 });
    }

    const model = getGeminiModel();

    if (externalContext.length && !isFirecrawlAvailable(subscriptionPlan)) {
      return NextResponse.json(
        {
          error:
            "External context enrichment is available on paid plans. Upgrade to include Firecrawl results.",
        },
        { status: 403 },
      );
    }

    try {
      recordUsageOrThrow(email, subscriptionPlan);
    } catch (usageError) {
      const message =
        usageError instanceof Error
          ? usageError.message
          : "Usage limit exceeded.";
      return NextResponse.json({ error: message }, { status: 429 });
    }

    const formattedQnA = questions
      .map((question) => {
        const answer = answers[question.id];
        return `Question (${question.id}): ${question.question}\nAnswer: ${answer ? answer.trim() : "[no answer supplied]"
          }`;
      })
      .join("\n\n");

    const blueprintJson = JSON.stringify(blueprint);
    const questionsJson = JSON.stringify(questions);
    const answersJson = JSON.stringify(answers);

    // Build output format instructions from selected options
    const outputFormatInstructions = outputFormats.length > 0
      ? `The response should be formatted as: ${outputFormats.join(", ")}`
      : "";

    const userPromptParts = [
      `<target_model>${targetModel}</target_model>`,
      `<original_prompt>${prompt}</original_prompt>`,
      `<extra_context>${context ?? ""}</extra_context>`,
      `<tone>${tone ?? ""}</tone>`,
      `<output_requirements>${outputFormatInstructions}</output_requirements>`,
      `<blueprint>${blueprintJson}</blueprint>`,
      `<questions>${questionsJson}</questions>`,
      `<answers>${answersJson}</answers>`,
      `<formatted_answers>${formattedQnA}</formatted_answers>`,
    ];

    if (externalContext.length) {
      const externalContextJson = JSON.stringify(externalContext);
      userPromptParts.push(`<external_context_raw>${externalContextJson}</external_context_raw>`);
      userPromptParts.push(formatExternalContext(externalContext));
    }

    if (variationHint) {
      userPromptParts.push(`<variation_hint>${variationHint}</variation_hint>`);
    }

    const userPrompt = userPromptParts.join("\n");

    const fewShotMessages = REFINER_FEW_SHOTS.flatMap(({ user, assistant }) => [
      { role: "user" as const, parts: [{ text: user }] },
      { role: "model" as const, parts: [{ text: assistant }] },
    ]);

    // Select system prompt based on modality
    const getRefinerSystemPrompt = (mod: string): string => {
      if (mod === "video") {
        return VIDEO_REFINER_SYSTEM_PROMPT;
      }
      if (mod === "image") {
        return IMAGE_REFINER_SYSTEM_PROMPT;
      }
      if (mod === "system") {
        return SYSTEM_PROMPT_REFINER;
      }
      return REFINER_SYSTEM_PROMPT;
    };

    const systemPrompt = getRefinerSystemPrompt(modality);

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
      generationConfig: {
        temperature: 0.4,
        topP: 0.9,
        responseMimeType: "application/json",
      },
    });

    const rawText = result.response.text();
    const parsed = extractJsonFromText<PromptRefinementResult>(rawText);
    const validationError = validateRefinementPayload(parsed);

    if (validationError) {
      return NextResponse.json(
        { error: `Invalid refinement response: ${validationError}` },
        { status: 502 },
      );
    }

    return NextResponse.json(parsed);
  } catch (error) {
    if (error instanceof SyntaxError) {
      return NextResponse.json(
        { error: "Failed to parse model response into JSON." },
        { status: 502 },
      );
    }

    const message =
      error instanceof Error ? error.message : "Unknown error occurred.";

    return NextResponse.json(
      { error: `Prompt refinement failed: ${message}` },
      { status: 500 },
    );
  }
}

function formatExternalContext(documents: RetrievedDocument[]): string {
  if (!documents.length) {
    return "";
  }

  const formatted = documents
    .map((doc, index) => {
      const snippet = doc.snippet.replace(/\s+/g, " ").trim();
      return `Result ${index + 1}:\nTitle: ${doc.title}\nURL: ${doc.url}\nSummary: ${snippet}`;
    })
    .join("\n\n");

  return `<external_context>${formatted}</external_context>`;
}
