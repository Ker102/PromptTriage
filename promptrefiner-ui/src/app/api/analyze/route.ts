import { NextResponse } from "next/server";
import { getGeminiModel, extractJsonFromText } from "@/lib/gemini";
import type {
  AnalyzeRequestPayload,
  PromptAnalysisResult,
  PromptBlueprint,
} from "@/types/prompt";
import {
  ANALYZER_FEW_SHOTS,
  ANALYZER_SYSTEM_PROMPT,
  PROMPT_VERSION,
} from "@/prompts/metaprompt";

const MIN_QUESTIONS = 2;

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
    const body = (await req.json()) as AnalyzeRequestPayload;
    const prompt = body.prompt?.trim();
    const targetModel = body.targetModel?.trim();
    const context = body.context?.trim();

    if (!prompt) {
      return NextResponse.json(
        { error: "Prompt text is required." },
        { status: 400 },
      );
    }

    if (!targetModel) {
      return NextResponse.json(
        { error: "Target model is required so we can tailor the refinement." },
        { status: 400 },
      );
    }

    const model = getGeminiModel();

    const userPrompt = [
      `<target_model>${targetModel}</target_model>`,
      `<original_prompt>${prompt}</original_prompt>`,
      `<extra_context>${context ?? ""}</extra_context>`,
    ].join("\n");

    const fewShotMessages = ANALYZER_FEW_SHOTS.flatMap(({ user, assistant }) => [
      { role: "user" as const, parts: [{ text: user }] },
      { role: "model" as const, parts: [{ text: assistant }] },
    ]);

    const result = await model.generateContent({
      systemInstruction: {
        role: "system",
        parts: [{ text: ANALYZER_SYSTEM_PROMPT }],
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
    const parsed = extractJsonFromText<PromptAnalysisResult>(rawText);
    const validationError = validateAnalysisPayload(parsed);

    if (validationError) {
      return NextResponse.json(
        { error: `Invalid analysis response: ${validationError}` },
        { status: 502 },
      );
    }

    return NextResponse.json(parsed);
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
